"""Tests for AUDIT-002: Audit logging service.

Covers: logging an action writes a row, optional fields default to None,
DB failure is swallowed and logged (non-fatal), AppError with correct code.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.backend.db.base import Base
from src.backend.models.audit_log import AuditLog
from src.backend.services.auth.audit_service import AuditService


@pytest.fixture()
def db_session() -> Session:
    """Create an in-memory SQLite session with schema translation."""
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


class TestAuditServiceLog:
    """AuditService.log() writes rows to the AuditLog table."""

    def test_log_writes_row(self, db_session: Session) -> None:
        service = AuditService(db_session)
        service.log(
            action="scan_completed",
            resource_type="scan",
            resource_id="scan-001",
            change_summary="Scanned 10 URLs",
            user_id="user-abc",
            ip_address="10.0.0.1",
        )

        rows = db_session.query(AuditLog).all()
        assert len(rows) == 1
        row = rows[0]
        assert row.action == "scan_completed"
        assert row.resource_type == "scan"
        assert row.resource_id == "scan-001"
        assert row.change_summary == "Scanned 10 URLs"
        assert row.user_id == "user-abc"
        assert row.ip_address == "10.0.0.1"
        assert row.id is not None
        assert isinstance(row.id, uuid.UUID)
        assert row.created_at is not None

    def test_log_multiple_rows(self, db_session: Session) -> None:
        service = AuditService(db_session)
        service.log(
            action="opportunity_acted",
            resource_type="opportunity",
            resource_id="opp-1",
        )
        service.log(
            action="digest_sent",
            resource_type="digest",
            resource_id="dig-1",
        )

        rows = db_session.query(AuditLog).all()
        assert len(rows) == 2


class TestAuditServiceOptionalFields:
    """user_id and ip_address are optional (system actions)."""

    def test_user_id_defaults_to_none(self, db_session: Session) -> None:
        service = AuditService(db_session)
        service.log(
            action="scan_completed",
            resource_type="scan",
            resource_id="scan-002",
        )

        row = db_session.query(AuditLog).one()
        assert row.user_id is None

    def test_ip_address_defaults_to_none(self, db_session: Session) -> None:
        service = AuditService(db_session)
        service.log(
            action="scan_completed",
            resource_type="scan",
            resource_id="scan-003",
        )

        row = db_session.query(AuditLog).one()
        assert row.ip_address is None

    def test_change_summary_defaults_to_none(
        self, db_session: Session
    ) -> None:
        service = AuditService(db_session)
        service.log(
            action="scan_completed",
            resource_type="scan",
        )

        row = db_session.query(AuditLog).one()
        assert row.change_summary is None

    def test_resource_id_defaults_to_none(
        self, db_session: Session
    ) -> None:
        service = AuditService(db_session)
        service.log(
            action="scan_completed",
            resource_type="scan",
        )

        row = db_session.query(AuditLog).one()
        assert row.resource_id is None


class TestAuditServiceDbFailure:
    """DB insert failure is logged but does not raise."""

    def test_db_failure_does_not_raise(self, db_session: Session) -> None:
        service = AuditService(db_session)

        with patch.object(
            db_session, "flush", side_effect=RuntimeError("db gone")
        ):
            service.log(
                action="scan_completed",
                resource_type="scan",
                resource_id="scan-fail",
            )

    @patch("src.backend.services.auth.audit_service.log")
    def test_db_failure_logs_error(
        self, mock_log: MagicMock, db_session: Session
    ) -> None:
        service = AuditService(db_session)

        with patch.object(
            db_session, "flush", side_effect=RuntimeError("db gone")
        ):
            service.log(
                action="scan_completed",
                resource_type="scan",
                resource_id="scan-fail",
            )

        mock_log.error.assert_called_once()
        call_args = mock_log.error.call_args
        assert call_args[1]["extra"]["error_code"] == "AUDIT_LOG_ERROR"
