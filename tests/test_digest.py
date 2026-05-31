"""Tests for DELIV-001: Digest builder.

Covers: build_digest renders each opportunity (url, why_matched, draft_reply)
into plain-text + HTML, empty input yields a valid empty digest,
fetch_new_opportunities only returns status='new' rows with optional
niche filter, and the Digest contract fields.
"""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from contracts.delivery.digest import Digest
from contracts.opportunity.opportunity import OpportunityData
from src.backend.db.base import Base
from src.backend.models.opportunity import Opportunity, OpportunityStatus
from src.backend.services.delivery.digest import (
    build_digest,
    fetch_new_opportunities,
)

# -- fixtures ----------------------------------------------------------------

@pytest.fixture()
def db_session() -> Session:
    """In-memory SQLite session with buzzreach schema attached."""
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


def _make_opportunity(**overrides: object) -> Opportunity:
    """Build an Opportunity with sensible defaults; override any field."""
    defaults: dict[str, object] = {
        "niche": "tax",
        "url": "https://reddit.com/r/tax/comments/abc123",
        "title": "How do I reduce my IRS penalty?",
        "source": "reddit",
        "why_matched": "User asking about IRS penalty reduction",
        "relevance_score": 0.85,
        "draft_reply": "You might want to check out the first-time abatement...",
    }
    defaults.update(overrides)
    return Opportunity(**defaults)


def _opportunity_data(**overrides: object) -> OpportunityData:
    """Build an OpportunityData DTO with sensible defaults."""
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "niche": "tax",
        "url": "https://reddit.com/r/tax/comments/abc123",
        "title": "How do I reduce my IRS penalty?",
        "source": "reddit",
        "why_matched": "User asking about IRS penalty reduction",
        "relevance_score": 0.85,
        "draft_reply": "Check out the first-time abatement option.",
        "status": "new",
        "created_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return OpportunityData(**defaults)


# -- build_digest: non-empty input -------------------------------------------

class TestBuildDigestWithOpportunities:
    """build_digest renders each opportunity into text + HTML."""

    def test_digest_contains_each_url(self) -> None:
        opps = [
            _opportunity_data(url="https://reddit.com/r/tax/1"),
            _opportunity_data(url="https://reddit.com/r/tax/2"),
        ]
        digest = build_digest(opps)

        assert "https://reddit.com/r/tax/1" in digest.text_body
        assert "https://reddit.com/r/tax/2" in digest.text_body
        assert "https://reddit.com/r/tax/1" in digest.html_body
        assert "https://reddit.com/r/tax/2" in digest.html_body

    def test_digest_contains_why_matched(self) -> None:
        opps = [_opportunity_data(why_matched="Mentions IRS penalty")]
        digest = build_digest(opps)

        assert "Mentions IRS penalty" in digest.text_body
        assert "Mentions IRS penalty" in digest.html_body

    def test_digest_contains_full_draft_reply(self) -> None:
        draft = "Here is a detailed reply about penalty abatement."
        opps = [_opportunity_data(draft_reply=draft)]
        digest = build_digest(opps)

        assert draft in digest.text_body
        assert draft in digest.html_body

    def test_digest_contains_relevance_score(self) -> None:
        opps = [_opportunity_data(relevance_score=0.92)]
        digest = build_digest(opps)

        assert "0.92" in digest.text_body

    def test_digest_opportunity_ids_match(self) -> None:
        id1, id2 = uuid.uuid4(), uuid.uuid4()
        opps = [_opportunity_data(id=id1), _opportunity_data(id=id2)]
        digest = build_digest(opps)

        assert set(digest.opportunity_ids) == {id1, id2}

    def test_digest_subject_includes_count(self) -> None:
        opps = [_opportunity_data(), _opportunity_data()]
        digest = build_digest(opps)

        assert "2" in digest.subject

    def test_digest_returns_digest_type(self) -> None:
        opps = [_opportunity_data()]
        digest = build_digest(opps)

        assert isinstance(digest, Digest)


# -- build_digest: empty input -----------------------------------------------

class TestBuildDigestEmpty:
    """Empty input produces a valid empty digest (no crash)."""

    def test_empty_list_returns_valid_digest(self) -> None:
        digest = build_digest([])

        assert isinstance(digest, Digest)
        assert digest.opportunity_ids == []

    def test_empty_digest_has_subject(self) -> None:
        digest = build_digest([])

        assert digest.subject != ""

    def test_empty_digest_has_text_body(self) -> None:
        digest = build_digest([])

        assert isinstance(digest.text_body, str)

    def test_empty_digest_has_html_body(self) -> None:
        digest = build_digest([])

        assert isinstance(digest.html_body, str)


# -- fetch_new_opportunities -------------------------------------------------

class TestFetchNewOpportunities:
    """fetch_new_opportunities only returns status='new' rows."""

    def test_returns_only_new_status(self, db_session: Session) -> None:
        new = _make_opportunity(url="https://example.com/new")
        delivered = _make_opportunity(
            url="https://example.com/delivered",
            status=OpportunityStatus.DELIVERED,
        )
        db_session.add_all([new, delivered])
        db_session.commit()

        result = fetch_new_opportunities(db_session)

        assert len(result) == 1
        assert result[0].url == "https://example.com/new"

    def test_returns_empty_when_no_new(self, db_session: Session) -> None:
        delivered = _make_opportunity(
            status=OpportunityStatus.DELIVERED,
        )
        db_session.add(delivered)
        db_session.commit()

        result = fetch_new_opportunities(db_session)

        assert result == []

    def test_returns_multiple_new(self, db_session: Session) -> None:
        for i in range(3):
            db_session.add(
                _make_opportunity(url=f"https://example.com/{i}"),
            )
        db_session.commit()

        result = fetch_new_opportunities(db_session)

        assert len(result) == 3

    def test_filters_by_niche(self, db_session: Session) -> None:
        db_session.add(_make_opportunity(niche="tax"))
        db_session.add(_make_opportunity(
            niche="parking",
            url="https://example.com/parking",
        ))
        db_session.commit()

        result = fetch_new_opportunities(db_session, niche="parking")

        assert len(result) == 1
        assert result[0].niche == "parking"

    def test_niche_none_returns_all_new(self, db_session: Session) -> None:
        db_session.add(_make_opportunity(niche="tax"))
        db_session.add(_make_opportunity(
            niche="parking",
            url="https://example.com/parking",
        ))
        db_session.commit()

        result = fetch_new_opportunities(db_session, niche=None)

        assert len(result) == 2

    def test_returns_opportunity_data_type(self, db_session: Session) -> None:
        db_session.add(_make_opportunity())
        db_session.commit()

        result = fetch_new_opportunities(db_session)

        assert len(result) == 1
        assert isinstance(result[0], OpportunityData)


# -- Digest contract ----------------------------------------------------------

class TestDigestContract:
    """Digest contract fields match the spec."""

    def test_contract_fields(self) -> None:
        expected = {"subject", "text_body", "html_body", "opportunity_ids"}
        assert set(Digest.model_fields.keys()) == expected
