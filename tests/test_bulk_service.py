"""Tests for FEAT-006: Bulk Actions Service (L2).

Covers: bulk_archive, bulk_regenerate, bulk_export_csv, bulk_delete,
nonexistent ID handling, CSV format validation.
"""

import uuid

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.db.base import Base
from src.backend.errors import AppError
from src.backend.models.opportunity import Opportunity, OpportunityStatus
from src.backend.services.bulk_actions import (
    bulk_archive,
    bulk_delete,
    bulk_export_csv,
    bulk_regenerate,
)


@pytest.fixture()
def db_session() -> Session:
    """In-memory SQLite session with cross-thread access."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        execution_options={"schema_translate_map": {"buzzreach": None}},
        poolclass=StaticPool,
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


def _make_opportunity(
    db_session: Session,
    **overrides: object,
) -> Opportunity:
    """Create and persist an opportunity."""
    defaults: dict[str, object] = {
        "niche": "tax-help",
        "url": "https://reddit.com/r/tax/123",
        "title": "Need help with IRS penalty",
        "source": "reddit",
        "why_matched": "User asking about IRS penalties",
        "relevance_score": 0.85,
        "draft_reply": "Here is how you can resolve this...",
        "status": OpportunityStatus.DELIVERED,
    }
    defaults.update(overrides)
    opp = Opportunity(**defaults)
    db_session.add(opp)
    db_session.commit()
    return opp


class TestBulkArchiveService:
    """bulk_archive sets status to SKIPPED."""

    def test_archives_multiple(self, db_session: Session) -> None:
        opp1 = _make_opportunity(db_session)
        opp2 = _make_opportunity(db_session)
        user_id = uuid.uuid4()

        result = bulk_archive(
            db_session, [opp1.id, opp2.id], user_id,
        )
        assert result.processed == 2
        assert result.action == "archive"

        db_session.refresh(opp1)
        db_session.refresh(opp2)
        assert opp1.status == OpportunityStatus.SKIPPED
        assert opp2.status == OpportunityStatus.SKIPPED

    def test_nonexistent_ids_raises(
        self, db_session: Session,
    ) -> None:
        with pytest.raises(AppError) as exc_info:
            bulk_archive(
                db_session, [uuid.uuid4()], uuid.uuid4(),
            )
        assert exc_info.value.code == "NO_OPPORTUNITIES_FOUND"


class TestBulkRegenerateService:
    """bulk_regenerate clears edited_draft."""

    def test_clears_edited_draft(self, db_session: Session) -> None:
        opp = _make_opportunity(
            db_session, edited_draft="custom text",
        )
        user_id = uuid.uuid4()

        result = bulk_regenerate(db_session, [opp.id], user_id)
        assert result.processed == 1
        assert result.action == "regenerate"

        db_session.refresh(opp)
        assert opp.edited_draft is None


class TestBulkExportService:
    """bulk_export_csv returns valid CSV content."""

    def test_csv_has_header_and_data(
        self, db_session: Session,
    ) -> None:
        opp = _make_opportunity(db_session, title="Export Test")
        user_id = uuid.uuid4()

        csv_content = bulk_export_csv(db_session, [opp.id], user_id)
        lines = csv_content.strip().splitlines()

        assert lines[0] == "URL,Title,Platform,Score,Draft,Status,Date"
        assert "Export Test" in lines[1]
        assert "reddit" in lines[1]

    def test_csv_multiple_rows(self, db_session: Session) -> None:
        opp1 = _make_opportunity(db_session, title="Row1")
        opp2 = _make_opportunity(db_session, title="Row2")
        user_id = uuid.uuid4()

        csv_content = bulk_export_csv(
            db_session, [opp1.id, opp2.id], user_id,
        )
        lines = csv_content.strip().splitlines()
        assert len(lines) == 3  # header + 2 data rows


class TestBulkDeleteService:
    """bulk_delete soft-deletes by setting status and delivered_at."""

    def test_soft_deletes(self, db_session: Session) -> None:
        opp = _make_opportunity(db_session)
        user_id = uuid.uuid4()

        result = bulk_delete(db_session, [opp.id], user_id)
        assert result.processed == 1
        assert result.action == "delete"

        db_session.refresh(opp)
        assert opp.status == OpportunityStatus.SKIPPED
        assert opp.delivered_at is not None
