"""Tests for CORE-004: AuditLog model (compliance & security).

Covers: insert an audit log row, immutability (no update/delete via ORM),
required fields, nullable fields, default created_at, composite index,
and schema qualification.
"""

import uuid

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.backend.db.base import Base
from src.backend.models.audit_log import AuditLog


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


def _make_audit_log(**overrides: object) -> AuditLog:
    """Build an AuditLog with sensible defaults; override any field."""
    defaults: dict[str, object] = {
        "action": "opportunity_acted",
        "resource_type": "opportunity",
    }
    defaults.update(overrides)
    return AuditLog(**defaults)


class TestAuditLogCreate:
    """Creating an AuditLog row persists all columns correctly."""

    def test_create_with_defaults(self, db_session: Session) -> None:
        row = _make_audit_log()
        db_session.add(row)
        db_session.commit()

        assert row.id is not None
        assert isinstance(row.id, uuid.UUID)
        assert row.action == "opportunity_acted"
        assert row.resource_type == "opportunity"
        assert row.created_at is not None

    def test_resource_id_nullable(self, db_session: Session) -> None:
        row = _make_audit_log()
        db_session.add(row)
        db_session.commit()

        assert row.resource_id is None

    def test_change_summary_nullable(self, db_session: Session) -> None:
        row = _make_audit_log()
        db_session.add(row)
        db_session.commit()

        assert row.change_summary is None

    def test_user_id_nullable(self, db_session: Session) -> None:
        row = _make_audit_log()
        db_session.add(row)
        db_session.commit()

        assert row.user_id is None

    def test_ip_address_nullable(self, db_session: Session) -> None:
        row = _make_audit_log()
        db_session.add(row)
        db_session.commit()

        assert row.ip_address is None

    def test_stores_all_fields(self, db_session: Session) -> None:
        row = _make_audit_log(
            action="scan_completed",
            resource_type="scan",
            resource_id="abc-123",
            change_summary="Scanned 42 URLs",
            user_id="user-456",
            ip_address="192.168.1.1",
        )
        db_session.add(row)
        db_session.commit()

        fetched = db_session.get(AuditLog, row.id)
        assert fetched is not None
        assert fetched.action == "scan_completed"
        assert fetched.resource_type == "scan"
        assert fetched.resource_id == "abc-123"
        assert fetched.change_summary == "Scanned 42 URLs"
        assert fetched.user_id == "user-456"
        assert fetched.ip_address == "192.168.1.1"


class TestAuditLogImmutable:
    """AuditLog rows must be immutable — no UPDATE or DELETE via ORM."""

    def test_update_raises(self, db_session: Session) -> None:
        row = _make_audit_log()
        db_session.add(row)
        db_session.commit()

        row.action = "tampered"
        with pytest.raises(RuntimeError, match="immutable"):
            db_session.flush()

    def test_delete_raises(self, db_session: Session) -> None:
        row = _make_audit_log()
        db_session.add(row)
        db_session.commit()

        db_session.delete(row)
        with pytest.raises(RuntimeError, match="immutable"):
            db_session.flush()


class TestAuditLogIndex:
    """Composite index on (created_at, action) exists for query performance."""

    def test_composite_index_exists(self) -> None:
        index_names = {idx.name for idx in AuditLog.__table__.indexes}
        assert "ix_audit_logs_created_at_action" in index_names


class TestSchemaQualified:
    """AuditLog model is schema-qualified to 'buzzreach'."""

    def test_table_schema_is_buzzreach(self) -> None:
        args = AuditLog.__table_args__
        if isinstance(args, tuple):
            schema_dict = next(a for a in args if isinstance(a, dict))
        else:
            schema_dict = args
        assert schema_dict["schema"] == "buzzreach"

    def test_tablename_is_audit_logs(self) -> None:
        assert AuditLog.__tablename__ == "audit_logs"
