"""Tests for FILT-001: Dedup service (SQL lookup).

Covers:
- filter_unseen removes candidates whose (url, niche) already exists
- filter_unseen keeps candidates not yet seen
- mark_seen inserts a new row
- mark_seen is idempotent on (url, niche) — no duplicate rows
- Tests run against a real SQLite session
"""

from datetime import datetime

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker

from contracts.discovery.candidate import Candidate
from src.backend.db.base import Base
from src.backend.models.seen_url import SeenUrl
from src.backend.services.filter.dedup import filter_unseen, mark_seen


@pytest.fixture()
def db_session() -> Session:
    """In-memory SQLite session with the buzzreach schema attached."""
    engine = create_engine(
        "sqlite:///:memory:",
        execution_options={"schema_translate_map": {"buzzreach": None}},
    )

    @event.listens_for(engine, "connect")
    def _attach(dbapi_conn: object, _rec: object) -> None:
        cursor = dbapi_conn.cursor()  # type: ignore[union-attr]
        cursor.execute("ATTACH DATABASE ':memory:' AS buzzreach")
        cursor.close()

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()
    yield session
    session.close()
    engine.dispose()


def _make_candidate(url: str = "https://reddit.com/r/tax/abc") -> Candidate:
    """Build a Candidate with sensible defaults."""
    return Candidate(
        url=url,
        title="Test post",
        snippet="Need help with tax penalty",
        source="reddit.com",
        found_at=datetime(2026, 1, 15, 12, 0, 0),
    )


class TestFilterUnseen:
    """filter_unseen drops candidates already in seen_urls for a niche."""

    def test_all_new_candidates_kept(self, db_session: Session) -> None:
        candidates = [
            _make_candidate("https://reddit.com/r/tax/1"),
            _make_candidate("https://reddit.com/r/tax/2"),
        ]
        result = filter_unseen(candidates, niche="tax", session=db_session)
        assert len(result) == 2

    def test_seen_candidate_removed(self, db_session: Session) -> None:
        db_session.add(SeenUrl(url="https://reddit.com/r/tax/1", niche="tax"))
        db_session.commit()

        candidates = [
            _make_candidate("https://reddit.com/r/tax/1"),
            _make_candidate("https://reddit.com/r/tax/2"),
        ]
        result = filter_unseen(candidates, niche="tax", session=db_session)

        assert len(result) == 1
        assert result[0].url == "https://reddit.com/r/tax/2"

    def test_all_seen_returns_empty(self, db_session: Session) -> None:
        db_session.add(SeenUrl(url="https://reddit.com/r/tax/1", niche="tax"))
        db_session.add(SeenUrl(url="https://reddit.com/r/tax/2", niche="tax"))
        db_session.commit()

        candidates = [
            _make_candidate("https://reddit.com/r/tax/1"),
            _make_candidate("https://reddit.com/r/tax/2"),
        ]
        result = filter_unseen(candidates, niche="tax", session=db_session)
        assert result == []

    def test_different_niche_not_filtered(self, db_session: Session) -> None:
        db_session.add(
            SeenUrl(url="https://reddit.com/r/tax/1", niche="parking"),
        )
        db_session.commit()

        candidates = [_make_candidate("https://reddit.com/r/tax/1")]
        result = filter_unseen(candidates, niche="tax", session=db_session)
        assert len(result) == 1

    def test_empty_candidates_returns_empty(self, db_session: Session) -> None:
        result = filter_unseen([], niche="tax", session=db_session)
        assert result == []


class TestMarkSeen:
    """mark_seen inserts a row and is idempotent on (url, niche)."""

    def test_inserts_new_row(self, db_session: Session) -> None:
        mark_seen(
            url="https://reddit.com/r/tax/new",
            niche="tax",
            angle_covered="penalty advice",
            shown_to="user@test.com",
            session=db_session,
        )

        rows = db_session.execute(select(SeenUrl)).scalars().all()
        assert len(rows) == 1
        assert rows[0].url == "https://reddit.com/r/tax/new"
        assert rows[0].niche == "tax"
        assert rows[0].angle_covered == "penalty advice"
        assert rows[0].shown_to == "user@test.com"

    def test_idempotent_on_url_niche(self, db_session: Session) -> None:
        mark_seen(
            url="https://reddit.com/r/tax/1",
            niche="tax",
            angle_covered="angle A",
            shown_to="user1@test.com",
            session=db_session,
        )
        mark_seen(
            url="https://reddit.com/r/tax/1",
            niche="tax",
            angle_covered="angle B",
            shown_to="user2@test.com",
            session=db_session,
        )

        rows = db_session.execute(select(SeenUrl)).scalars().all()
        assert len(rows) == 1

    def test_same_url_different_niche_creates_two(
        self, db_session: Session
    ) -> None:
        mark_seen(
            url="https://reddit.com/r/tax/1",
            niche="tax",
            session=db_session,
        )
        mark_seen(
            url="https://reddit.com/r/tax/1",
            niche="parking",
            session=db_session,
        )

        rows = db_session.execute(select(SeenUrl)).scalars().all()
        assert len(rows) == 2

    def test_nullable_fields_default_to_none(
        self, db_session: Session
    ) -> None:
        mark_seen(
            url="https://reddit.com/r/tax/1",
            niche="tax",
            session=db_session,
        )

        row = db_session.execute(select(SeenUrl)).scalar_one()
        assert row.angle_covered is None
        assert row.shown_to is None
