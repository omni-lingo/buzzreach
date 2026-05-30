"""Tests for CORE-003: Opportunity model + OpportunityData contract.

Covers: insert a row, status transitions (new -> delivered -> acted/skipped),
OpportunityData.model_validate round-trip, schema qualification,
and enum constraint enforcement.
"""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from contracts.opportunity.opportunity import OpportunityData
from src.backend.db.base import Base
from src.backend.models.opportunity import Opportunity, OpportunityStatus


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


class TestOpportunityCreate:
    """Creating an Opportunity row persists all columns correctly."""

    def test_create_with_defaults(self, db_session: Session) -> None:
        row = _make_opportunity()
        db_session.add(row)
        db_session.commit()

        assert row.id is not None
        assert isinstance(row.id, uuid.UUID)
        assert row.niche == "tax"
        assert row.url == "https://reddit.com/r/tax/comments/abc123"
        assert row.title == "How do I reduce my IRS penalty?"
        assert row.source == "reddit"
        assert row.why_matched == "User asking about IRS penalty reduction"
        assert row.relevance_score == 0.85
        assert row.created_at is not None

    def test_default_status_is_new(self, db_session: Session) -> None:
        row = _make_opportunity()
        db_session.add(row)
        db_session.commit()

        assert row.status == OpportunityStatus.NEW

    def test_delivered_at_nullable(self, db_session: Session) -> None:
        row = _make_opportunity()
        db_session.add(row)
        db_session.commit()

        assert row.delivered_at is None

    def test_delivered_at_stores_value(self, db_session: Session) -> None:
        now = datetime.now(UTC)
        row = _make_opportunity(delivered_at=now)
        db_session.add(row)
        db_session.commit()

        fetched = db_session.get(Opportunity, row.id)
        assert fetched is not None
        assert fetched.delivered_at is not None


class TestStatusTransitions:
    """Status transitions between new, delivered, acted, and skipped."""

    def test_transition_new_to_delivered(self, db_session: Session) -> None:
        row = _make_opportunity()
        db_session.add(row)
        db_session.commit()

        row.status = OpportunityStatus.DELIVERED
        row.delivered_at = datetime.now(UTC)
        db_session.commit()

        fetched = db_session.get(Opportunity, row.id)
        assert fetched is not None
        assert fetched.status == OpportunityStatus.DELIVERED
        assert fetched.delivered_at is not None

    def test_transition_delivered_to_acted(self, db_session: Session) -> None:
        row = _make_opportunity(status=OpportunityStatus.DELIVERED)
        db_session.add(row)
        db_session.commit()

        row.status = OpportunityStatus.ACTED
        db_session.commit()

        fetched = db_session.get(Opportunity, row.id)
        assert fetched is not None
        assert fetched.status == OpportunityStatus.ACTED

    def test_transition_delivered_to_skipped(self, db_session: Session) -> None:
        row = _make_opportunity(status=OpportunityStatus.DELIVERED)
        db_session.add(row)
        db_session.commit()

        row.status = OpportunityStatus.SKIPPED
        db_session.commit()

        fetched = db_session.get(Opportunity, row.id)
        assert fetched is not None
        assert fetched.status == OpportunityStatus.SKIPPED

    def test_all_four_status_values_valid(self, db_session: Session) -> None:
        for status in OpportunityStatus:
            row = _make_opportunity(
                url=f"https://reddit.com/r/tax/{status.value}",
                status=status,
            )
            db_session.add(row)
        db_session.commit()

        count = db_session.query(Opportunity).count()
        assert count == 4

    def test_enum_constrains_values(self) -> None:
        valid = {e.value for e in OpportunityStatus}
        assert valid == {"new", "delivered", "acted", "skipped"}

    def test_invalid_status_not_in_enum(self) -> None:
        values = [e.value for e in OpportunityStatus]
        assert "invalid_status" not in values


class TestOpportunityDataContract:
    """OpportunityData contract mirrors the row shape for cross-module use."""

    def test_contract_from_persisted_row(self, db_session: Session) -> None:
        row = _make_opportunity()
        db_session.add(row)
        db_session.commit()

        data = OpportunityData.model_validate(row, from_attributes=True)
        assert data.id == row.id
        assert data.niche == row.niche
        assert data.url == row.url
        assert data.title == row.title
        assert data.source == row.source
        assert data.why_matched == row.why_matched
        assert data.relevance_score == row.relevance_score
        assert data.draft_reply == row.draft_reply
        assert data.status == OpportunityStatus.NEW.value

    def test_contract_round_trip(self, db_session: Session) -> None:
        row = _make_opportunity(
            status=OpportunityStatus.DELIVERED,
            delivered_at=datetime.now(UTC),
        )
        db_session.add(row)
        db_session.commit()

        data = OpportunityData.model_validate(row, from_attributes=True)
        serialized = data.model_dump()

        assert serialized["niche"] == "tax"
        assert serialized["source"] == "reddit"
        assert serialized["status"] == "delivered"
        assert serialized["delivered_at"] is not None

    def test_contract_fields_match_spec(self) -> None:
        expected = {
            "id", "niche", "url", "title", "source",
            "why_matched", "relevance_score", "draft_reply",
            "status", "created_at", "delivered_at",
        }
        assert set(OpportunityData.model_fields.keys()) == expected


class TestSchemaQualified:
    """Opportunity model is schema-qualified to 'buzzreach'."""

    def test_table_schema_is_buzzreach(self) -> None:
        args = Opportunity.__table_args__
        if isinstance(args, tuple):
            schema_dict = next(a for a in args if isinstance(a, dict))
        else:
            schema_dict = args
        assert schema_dict["schema"] == "buzzreach"

    def test_tablename_is_opportunities(self) -> None:
        assert Opportunity.__tablename__ == "opportunities"
