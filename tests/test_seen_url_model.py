"""Tests for CORE-002: SeenUrl model (own-actions dedup table).

Covers: insert a SeenUrl row, unique constraint enforcement on (url, niche),
nullable fields, default created_at, and schema qualification.
"""

import uuid

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from src.backend.db.base import Base
from src.backend.models.seen_url import SeenUrl


@pytest.fixture()
def db_session() -> Session:
    """Create an in-memory SQLite session with the buzzreach schema attached."""
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


def _make_seen_url(**overrides: object) -> SeenUrl:
    """Build a SeenUrl with sensible defaults; override any field."""
    defaults: dict[str, object] = {
        "url": "https://reddit.com/r/tax/post123",
        "niche": "tax",
    }
    defaults.update(overrides)
    return SeenUrl(**defaults)


class TestSeenUrlCreate:
    """Creating a SeenUrl row persists all columns correctly."""

    def test_create_with_defaults(self, db_session: Session) -> None:
        row = _make_seen_url()
        db_session.add(row)
        db_session.commit()

        assert row.id is not None
        assert isinstance(row.id, uuid.UUID)
        assert row.url == "https://reddit.com/r/tax/post123"
        assert row.niche == "tax"
        assert row.created_at is not None

    def test_angle_covered_nullable(self, db_session: Session) -> None:
        row = _make_seen_url()
        db_session.add(row)
        db_session.commit()

        assert row.angle_covered is None

    def test_shown_to_nullable(self, db_session: Session) -> None:
        row = _make_seen_url()
        db_session.add(row)
        db_session.commit()

        assert row.shown_to is None

    def test_angle_covered_stores_value(self, db_session: Session) -> None:
        row = _make_seen_url(angle_covered="penalty abatement advice")
        db_session.add(row)
        db_session.commit()

        fetched = db_session.get(SeenUrl, row.id)
        assert fetched is not None
        assert fetched.angle_covered == "penalty abatement advice"

    def test_shown_to_stores_value(self, db_session: Session) -> None:
        row = _make_seen_url(shown_to="user@example.com")
        db_session.add(row)
        db_session.commit()

        fetched = db_session.get(SeenUrl, row.id)
        assert fetched is not None
        assert fetched.shown_to == "user@example.com"


class TestSeenUrlUniqueConstraint:
    """Unique constraint on (url, niche) prevents duplicate rows."""

    def test_duplicate_url_niche_raises(self, db_session: Session) -> None:
        db_session.add(_make_seen_url(url="https://r.com/1", niche="tax"))
        db_session.commit()

        db_session.add(_make_seen_url(url="https://r.com/1", niche="tax"))
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_same_url_different_niche_allowed(self, db_session: Session) -> None:
        db_session.add(_make_seen_url(url="https://r.com/1", niche="tax"))
        db_session.commit()

        db_session.add(_make_seen_url(url="https://r.com/1", niche="parking"))
        db_session.commit()

    def test_different_url_same_niche_allowed(self, db_session: Session) -> None:
        db_session.add(_make_seen_url(url="https://r.com/1", niche="tax"))
        db_session.commit()

        db_session.add(_make_seen_url(url="https://r.com/2", niche="tax"))
        db_session.commit()


class TestSchemaQualified:
    """SeenUrl model is schema-qualified to 'buzzreach'."""

    def test_table_schema_is_buzzreach(self) -> None:
        args = SeenUrl.__table_args__
        if isinstance(args, tuple):
            schema_dict = next(a for a in args if isinstance(a, dict))
        else:
            schema_dict = args
        assert schema_dict["schema"] == "buzzreach"

    def test_tablename_is_seen_urls(self) -> None:
        assert SeenUrl.__tablename__ == "seen_urls"
