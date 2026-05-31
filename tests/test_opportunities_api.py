"""Tests for API-001: Opportunities API.

Covers: JWT authentication (401 without token), list/filter opportunities,
act/skip actions with audit logging, rate limiting (429), unknown ID (404).
"""

import uuid
from unittest.mock import MagicMock

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
    """In-memory SQLite session with cross-thread access for TestClient."""
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
    rate_limiter_allows: bool = True,
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

    if not rate_limiter_allows:
        from src.backend.api.rate_limit_middleware import (
            get_rate_limiter,
        )

        mock_limiter = MagicMock()
        mock_limiter.check.return_value = False
        app.dependency_overrides[get_rate_limiter] = lambda: mock_limiter

    return TestClient(app)


class TestListOpportunitiesAuth:
    """GET /api/v1/opportunities requires a valid JWT."""

    def test_no_token_returns_401(self, db_session: Session) -> None:
        client = _build_client(db_session)
        resp = client.get("/api/v1/opportunities")
        assert resp.status_code == 401
        body = resp.json()
        assert body["detail"]["error_code"] == "AUTH_REQUIRED"

    def test_valid_token_returns_200(self, db_session: Session) -> None:
        user = _make_user(db_session)
        _make_opportunity(db_session)
        client = _build_client(db_session, user=_make_user_data(user))
        resp = client.get("/api/v1/opportunities")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) == 1


class TestListOpportunitiesFilter:
    """GET /api/v1/opportunities?niche=X filters results."""

    def test_filter_by_niche(self, db_session: Session) -> None:
        user = _make_user(db_session)
        _make_opportunity(db_session, niche="tax-help")
        _make_opportunity(db_session, niche="parking")
        client = _build_client(db_session, user=_make_user_data(user))

        resp = client.get("/api/v1/opportunities?niche=parking")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 1
        assert items[0]["niche"] == "parking"

    def test_filter_by_status(self, db_session: Session) -> None:
        user = _make_user(db_session)
        _make_opportunity(
            db_session, status=OpportunityStatus.DELIVERED,
        )
        _make_opportunity(
            db_session, status=OpportunityStatus.ACTED,
        )
        client = _build_client(db_session, user=_make_user_data(user))

        resp = client.get("/api/v1/opportunities?status=acted")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 1
        assert items[0]["status"] == "acted"


class TestActEndpoint:
    """POST /api/v1/opportunities/{id}/act marks as acted."""

    def test_act_requires_auth(self, db_session: Session) -> None:
        opp = _make_opportunity(db_session)
        client = _build_client(db_session)
        resp = client.post(f"/api/v1/opportunities/{opp.id}/act")
        assert resp.status_code == 401

    def test_act_success(self, db_session: Session) -> None:
        user = _make_user(db_session)
        opp = _make_opportunity(db_session)
        client = _build_client(db_session, user=_make_user_data(user))
        resp = client.post(f"/api/v1/opportunities/{opp.id}/act")
        assert resp.status_code == 200
        assert resp.json()["status"] == "acted"

    def test_act_unknown_id_returns_404(
        self, db_session: Session,
    ) -> None:
        user = _make_user(db_session)
        fake_id = uuid.uuid4()
        client = _build_client(db_session, user=_make_user_data(user))
        resp = client.post(f"/api/v1/opportunities/{fake_id}/act")
        assert resp.status_code == 404
        body = resp.json()
        assert body["detail"]["error_code"] == "OPPORTUNITY_NOT_FOUND"

    def test_act_is_audit_logged(self, db_session: Session) -> None:
        user = _make_user(db_session)
        opp = _make_opportunity(db_session)
        client = _build_client(db_session, user=_make_user_data(user))
        client.post(f"/api/v1/opportunities/{opp.id}/act")

        logs = db_session.query(AuditLog).all()
        assert len(logs) == 1
        assert logs[0].action == "opportunity_acted"
        assert logs[0].user_id == str(user.id)
        assert logs[0].resource_id == str(opp.id)


class TestSkipEndpoint:
    """POST /api/v1/opportunities/{id}/skip marks as skipped."""

    def test_skip_requires_auth(self, db_session: Session) -> None:
        opp = _make_opportunity(db_session)
        client = _build_client(db_session)
        resp = client.post(f"/api/v1/opportunities/{opp.id}/skip")
        assert resp.status_code == 401

    def test_skip_success(self, db_session: Session) -> None:
        user = _make_user(db_session)
        opp = _make_opportunity(db_session)
        client = _build_client(db_session, user=_make_user_data(user))
        resp = client.post(f"/api/v1/opportunities/{opp.id}/skip")
        assert resp.status_code == 200
        assert resp.json()["status"] == "skipped"

    def test_skip_unknown_id_returns_404(
        self, db_session: Session,
    ) -> None:
        user = _make_user(db_session)
        fake_id = uuid.uuid4()
        client = _build_client(db_session, user=_make_user_data(user))
        resp = client.post(f"/api/v1/opportunities/{fake_id}/skip")
        assert resp.status_code == 404
        body = resp.json()
        assert body["detail"]["error_code"] == "OPPORTUNITY_NOT_FOUND"

    def test_skip_is_audit_logged(self, db_session: Session) -> None:
        user = _make_user(db_session)
        opp = _make_opportunity(db_session)
        client = _build_client(db_session, user=_make_user_data(user))
        client.post(f"/api/v1/opportunities/{opp.id}/skip")

        logs = db_session.query(AuditLog).all()
        assert len(logs) == 1
        assert logs[0].action == "opportunity_skipped"
        assert logs[0].user_id == str(user.id)


class TestRateLimiting:
    """Rate limiter returns 429 when quota exceeded."""

    def test_rate_limit_returns_429(self, db_session: Session) -> None:
        user = _make_user(db_session)
        client = _build_client(
            db_session,
            user=_make_user_data(user),
            rate_limiter_allows=False,
        )
        resp = client.get("/api/v1/opportunities")
        assert resp.status_code == 429
        body = resp.json()
        assert body["detail"]["error_code"] == "RATE_LIMIT_EXCEEDED"
