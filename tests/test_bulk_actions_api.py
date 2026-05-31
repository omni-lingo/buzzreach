"""Tests for FEAT-006: Bulk Actions API.

Covers: bulk archive, bulk regenerate, bulk export CSV, bulk delete,
auth requirements, empty IDs validation, audit logging.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from contracts.auth.user import UserData
from src.backend.db.base import Base
from src.backend.models.audit_log import AuditLog
from src.backend.models.opportunity import Opportunity, OpportunityStatus
from src.backend.models.user import User


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


def _make_user(db_session: Session) -> User:
    """Create and persist a test user."""
    user = User(
        username=f"user_{uuid.uuid4().hex[:8]}",
        email=f"{uuid.uuid4().hex[:8]}@test.com",
        password_hash="hashed_pw",
        api_key=f"bz_{uuid.uuid4().hex[:24]}",
    )
    db_session.add(user)
    db_session.commit()
    return user


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


def _make_user_data(user: User) -> UserData:
    """Build a UserData DTO from a User model."""
    return UserData(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=True,
    )


def _build_client(
    db_session: Session,
    user: UserData | None = None,
) -> TestClient:
    """Build a TestClient with mocked dependencies."""
    from src.backend.api.main import create_app

    app = create_app()

    if user is not None:
        from src.backend.api.auth_deps import get_current_user

        app.dependency_overrides[get_current_user] = lambda: user

    from src.backend.db.session import get_session

    def _override_session() -> Session:
        return db_session

    app.dependency_overrides[get_session] = _override_session
    return TestClient(app)


class TestBulkArchive:
    """POST /api/v1/opportunities/bulk/archive."""

    def test_archive_requires_auth(self, db_session: Session) -> None:
        opp = _make_opportunity(db_session)
        client = _build_client(db_session)
        resp = client.post(
            "/api/v1/opportunities/bulk/archive",
            json={"opportunity_ids": [str(opp.id)]},
        )
        assert resp.status_code == 401

    def test_archive_success(self, db_session: Session) -> None:
        user = _make_user(db_session)
        opp1 = _make_opportunity(db_session)
        opp2 = _make_opportunity(db_session)
        client = _build_client(db_session, user=_make_user_data(user))

        resp = client.post(
            "/api/v1/opportunities/bulk/archive",
            json={"opportunity_ids": [str(opp1.id), str(opp2.id)]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["processed"] == 2
        assert body["action"] == "archive"

    def test_archive_is_audit_logged(
        self, db_session: Session,
    ) -> None:
        user = _make_user(db_session)
        opp = _make_opportunity(db_session)
        client = _build_client(db_session, user=_make_user_data(user))
        client.post(
            "/api/v1/opportunities/bulk/archive",
            json={"opportunity_ids": [str(opp.id)]},
        )
        logs = db_session.query(AuditLog).all()
        assert any(a.action == "bulk_archive" for a in logs)


class TestBulkRegenerate:
    """POST /api/v1/opportunities/bulk/regenerate."""

    def test_regenerate_requires_auth(
        self, db_session: Session,
    ) -> None:
        opp = _make_opportunity(db_session)
        client = _build_client(db_session)
        resp = client.post(
            "/api/v1/opportunities/bulk/regenerate",
            json={"opportunity_ids": [str(opp.id)]},
        )
        assert resp.status_code == 401

    def test_regenerate_success(self, db_session: Session) -> None:
        user = _make_user(db_session)
        opp = _make_opportunity(
            db_session, edited_draft="custom text",
        )
        client = _build_client(db_session, user=_make_user_data(user))

        resp = client.post(
            "/api/v1/opportunities/bulk/regenerate",
            json={"opportunity_ids": [str(opp.id)]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["processed"] == 1
        assert body["action"] == "regenerate"


class TestBulkExport:
    """POST /api/v1/opportunities/bulk/export."""

    def test_export_requires_auth(self, db_session: Session) -> None:
        opp = _make_opportunity(db_session)
        client = _build_client(db_session)
        resp = client.post(
            "/api/v1/opportunities/bulk/export",
            json={"opportunity_ids": [str(opp.id)]},
        )
        assert resp.status_code == 401

    def test_export_returns_csv(self, db_session: Session) -> None:
        user = _make_user(db_session)
        opp = _make_opportunity(db_session, title="Test Opp")
        client = _build_client(db_session, user=_make_user_data(user))

        resp = client.post(
            "/api/v1/opportunities/bulk/export",
            json={"opportunity_ids": [str(opp.id)]},
        )
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert "opportunities_" in resp.headers["content-disposition"]
        lines = resp.text.strip().splitlines()
        assert lines[0] == "URL,Title,Platform,Score,Draft,Status,Date"
        assert "Test Opp" in lines[1]

    def test_export_nonexistent_returns_404(
        self, db_session: Session,
    ) -> None:
        user = _make_user(db_session)
        fake_id = uuid.uuid4()
        client = _build_client(db_session, user=_make_user_data(user))
        resp = client.post(
            "/api/v1/opportunities/bulk/export",
            json={"opportunity_ids": [str(fake_id)]},
        )
        assert resp.status_code == 404


class TestBulkDelete:
    """DELETE /api/v1/opportunities/bulk."""

    def test_delete_requires_auth(self, db_session: Session) -> None:
        opp = _make_opportunity(db_session)
        client = _build_client(db_session)
        resp = client.request(
            "DELETE",
            "/api/v1/opportunities/bulk",
            json={"opportunity_ids": [str(opp.id)]},
        )
        assert resp.status_code == 401

    def test_delete_success(self, db_session: Session) -> None:
        user = _make_user(db_session)
        opp = _make_opportunity(db_session)
        client = _build_client(db_session, user=_make_user_data(user))

        resp = client.request(
            "DELETE",
            "/api/v1/opportunities/bulk",
            json={"opportunity_ids": [str(opp.id)]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["processed"] == 1
        assert body["action"] == "delete"

    def test_delete_is_audit_logged(
        self, db_session: Session,
    ) -> None:
        user = _make_user(db_session)
        opp = _make_opportunity(db_session)
        client = _build_client(db_session, user=_make_user_data(user))
        client.request(
            "DELETE",
            "/api/v1/opportunities/bulk",
            json={"opportunity_ids": [str(opp.id)]},
        )
        logs = db_session.query(AuditLog).all()
        assert any(a.action == "bulk_delete" for a in logs)


class TestBulkValidation:
    """Validation edge cases for bulk endpoints."""

    def test_empty_ids_returns_422(self, db_session: Session) -> None:
        user = _make_user(db_session)
        client = _build_client(db_session, user=_make_user_data(user))
        resp = client.post(
            "/api/v1/opportunities/bulk/archive",
            json={"opportunity_ids": []},
        )
        assert resp.status_code == 422
