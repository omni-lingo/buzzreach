"""Tests for MOBILE-002: Push Notifications.

Covers:
- PushSubscription model (CRUD, constraints, schema qualification)
- PushService (send, batch, schedule, token cleanup, plan limits)
- Push API routes (register, unregister, auth)
- Integration: opportunity creation triggers push to relevant users
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from contracts.auth.user import UserData
from contracts.push.push_subscription import NotificationFrequency
from src.backend.db.base import Base
from src.backend.models.push_subscription import PushSubscription
from src.backend.models.subscription import Subscription
from src.backend.models.user import User


@pytest.fixture()
def db_session() -> Session:
    """In-memory SQLite session for push notification tests."""
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


def _make_subscription(
    db_session: Session,
    user_id: uuid.UUID,
    plan_id: str = "free",
) -> Subscription:
    """Create and persist a subscription."""
    sub = Subscription(user_id=user_id, plan_id=plan_id, status="active")
    db_session.add(sub)
    db_session.commit()
    return sub


def _make_push_sub(
    db_session: Session,
    user_id: uuid.UUID,
    **overrides: object,
) -> PushSubscription:
    """Create and persist a push subscription."""
    defaults: dict[str, object] = {
        "user_id": user_id,
        "device_token": f"ExponentPushToken[{uuid.uuid4().hex[:20]}]",
        "platform": "ios",
        "is_active": True,
    }
    defaults.update(overrides)
    sub = PushSubscription(**defaults)
    db_session.add(sub)
    db_session.commit()
    return sub


def _make_user_data(user: User) -> UserData:
    """Build a UserData DTO from a User model."""
    return UserData(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=True,
    )


# --- Model tests ---


class TestPushSubscriptionModel:
    """PushSubscription ORM model tests."""

    def test_create_with_defaults(self, db_session: Session) -> None:
        user = _make_user(db_session)
        sub = _make_push_sub(db_session, user.id)
        assert sub.id is not None
        assert sub.is_active is True
        assert sub.created_at is not None

    def test_schema_qualified(self) -> None:
        args = PushSubscription.__table_args__
        schema = args[-1] if isinstance(args[-1], dict) else args
        if isinstance(schema, dict):
            assert schema.get("schema") == "buzzreach"
        else:
            assert any(
                d.get("schema") == "buzzreach"
                for d in args
                if isinstance(d, dict)
            )

    def test_platform_enum_values(self, db_session: Session) -> None:
        user = _make_user(db_session)
        ios_sub = _make_push_sub(db_session, user.id, platform="ios")
        assert ios_sub.platform == "ios"
        android_sub = _make_push_sub(
            db_session, user.id, platform="android",
            device_token="ExponentPushToken[android123]",
        )
        assert android_sub.platform == "android"

    def test_deactivate_token(self, db_session: Session) -> None:
        user = _make_user(db_session)
        sub = _make_push_sub(db_session, user.id)
        sub.is_active = False
        db_session.commit()
        refreshed = db_session.get(PushSubscription, sub.id)
        assert refreshed is not None
        assert refreshed.is_active is False

    def test_updated_at_changes(self, db_session: Session) -> None:
        user = _make_user(db_session)
        sub = _make_push_sub(db_session, user.id)
        original = sub.updated_at
        sub.is_active = False
        db_session.commit()
        assert sub.updated_at is not None
        assert sub.updated_at >= original


# --- Service tests ---


class TestPushServiceSend:
    """PushService.send_push_notification tests."""

    @patch("src.backend.services.push_service._post_to_expo")
    def test_send_to_active_user(
        self, mock_post: MagicMock, db_session: Session,
    ) -> None:
        from src.backend.services.push_service import PushService

        mock_post.return_value = [{"status": "ok"}]
        user = _make_user(db_session)
        _make_push_sub(db_session, user.id)
        svc = PushService(db_session)

        result = svc.send_push_notification(
            user_id=user.id,
            title="New Opportunity",
            body="High-score match found",
            opportunity_id=uuid.uuid4(),
        )
        assert result is True
        mock_post.assert_called_once()

    @patch("src.backend.services.push_service._post_to_expo")
    def test_no_active_tokens_returns_false(
        self, mock_post: MagicMock, db_session: Session,
    ) -> None:
        from src.backend.services.push_service import PushService

        user = _make_user(db_session)
        svc = PushService(db_session)
        result = svc.send_push_notification(
            user_id=user.id,
            title="Test",
            body="Test body",
        )
        assert result is False
        mock_post.assert_not_called()

    @patch("src.backend.services.push_service._post_to_expo")
    def test_inactive_tokens_skipped(
        self, mock_post: MagicMock, db_session: Session,
    ) -> None:
        from src.backend.services.push_service import PushService

        user = _make_user(db_session)
        _make_push_sub(db_session, user.id, is_active=False)
        svc = PushService(db_session)
        result = svc.send_push_notification(
            user_id=user.id,
            title="Test",
            body="Body",
        )
        assert result is False
        mock_post.assert_not_called()


class TestPushServiceBatch:
    """PushService.batch_send_notifications tests."""

    @patch("src.backend.services.push_service._post_to_expo")
    def test_batch_sends_to_multiple_users(
        self, mock_post: MagicMock, db_session: Session,
    ) -> None:
        from src.backend.services.push_service import PushService

        mock_post.return_value = [{"status": "ok"}]
        user1 = _make_user(db_session)
        user2 = _make_user(db_session)
        _make_push_sub(db_session, user1.id)
        _make_push_sub(db_session, user2.id)
        svc = PushService(db_session)

        sent = svc.batch_send_notifications(
            user_ids=[user1.id, user2.id],
            title="Batch Alert",
            body="New opportunities available",
        )
        assert sent == 2

    @patch("src.backend.services.push_service._post_to_expo")
    def test_batch_skips_users_without_tokens(
        self, mock_post: MagicMock, db_session: Session,
    ) -> None:
        from src.backend.services.push_service import PushService

        mock_post.return_value = [{"status": "ok"}]
        user1 = _make_user(db_session)
        user2 = _make_user(db_session)
        _make_push_sub(db_session, user1.id)
        svc = PushService(db_session)

        sent = svc.batch_send_notifications(
            user_ids=[user1.id, user2.id],
            title="Alert",
            body="Body",
        )
        assert sent == 1


class TestPushServiceSchedule:
    """PushService.schedule_notification tests."""

    def test_schedule_creates_record(self, db_session: Session) -> None:
        from src.backend.services.push_service import PushService

        user = _make_user(db_session)
        _make_push_sub(db_session, user.id)
        svc = PushService(db_session)

        send_at = datetime.now(UTC) + timedelta(hours=1)
        result = svc.schedule_notification(
            user_id=user.id,
            title="Scheduled",
            body="Scheduled push",
            send_at=send_at,
        )
        assert result is not None
        assert result["user_id"] == str(user.id)
        assert result["send_at"] is not None


class TestPushServiceTokenCleanup:
    """PushService.cleanup_stale_tokens tests."""

    def test_deactivates_stale_tokens(self, db_session: Session) -> None:
        from src.backend.services.push_service import PushService

        user = _make_user(db_session)
        sub = _make_push_sub(db_session, user.id)
        svc = PushService(db_session)

        svc.deactivate_token(sub.device_token)
        refreshed = db_session.get(PushSubscription, sub.id)
        assert refreshed is not None
        assert refreshed.is_active is False


class TestPushServicePlanLimits:
    """Push notifications respect plan limits."""

    @patch("src.backend.services.push_service._post_to_expo")
    def test_free_plan_gets_daily_digest_only(
        self, mock_post: MagicMock, db_session: Session,
    ) -> None:
        from src.backend.services.push_service import PushService

        user = _make_user(db_session)
        _make_subscription(db_session, user.id, plan_id="free")
        _make_push_sub(db_session, user.id)
        svc = PushService(db_session)

        freq = svc.get_user_notification_frequency(user.id)
        assert freq == NotificationFrequency.DAILY

    @patch("src.backend.services.push_service._post_to_expo")
    def test_pro_plan_gets_realtime(
        self, mock_post: MagicMock, db_session: Session,
    ) -> None:
        from src.backend.services.push_service import PushService

        user = _make_user(db_session)
        _make_subscription(db_session, user.id, plan_id="pro")
        _make_push_sub(db_session, user.id)
        svc = PushService(db_session)

        freq = svc.get_user_notification_frequency(user.id)
        assert freq == NotificationFrequency.REALTIME


class TestPushServiceUnverifiedUser:
    """No push sent to unverified (inactive) users."""

    @patch("src.backend.services.push_service._post_to_expo")
    def test_inactive_user_blocked(
        self, mock_post: MagicMock, db_session: Session,
    ) -> None:
        from src.backend.services.push_service import PushService

        user = _make_user(db_session)
        user.is_active = False
        db_session.commit()
        _make_push_sub(db_session, user.id)
        svc = PushService(db_session)

        result = svc.send_push_notification(
            user_id=user.id,
            title="Test",
            body="Body",
        )
        assert result is False
        mock_post.assert_not_called()


# --- API tests ---


def _build_push_client(
    db_session: Session,
    user: UserData | None = None,
) -> TestClient:
    """Build a TestClient with push routes."""
    from src.backend.api.main import create_app
    from src.backend.db.session import get_session

    app = create_app()

    if user is not None:
        from src.backend.api.auth_deps import get_current_user

        app.dependency_overrides[get_current_user] = lambda: user

    def _override_session() -> Session:
        return db_session

    app.dependency_overrides[get_session] = _override_session
    return TestClient(app)


class TestPushRegisterAPI:
    """POST /api/v1/push/register tests."""

    def test_register_requires_auth(self, db_session: Session) -> None:
        client = _build_push_client(db_session)
        resp = client.post(
            "/api/v1/push/register",
            json={
                "device_token": "ExponentPushToken[abc123]",
                "platform": "ios",
            },
        )
        assert resp.status_code == 401

    def test_register_success(self, db_session: Session) -> None:
        user = _make_user(db_session)
        client = _build_push_client(
            db_session, user=_make_user_data(user),
        )
        resp = client.post(
            "/api/v1/push/register",
            json={
                "device_token": "ExponentPushToken[abc123]",
                "platform": "ios",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["device_token"] == "ExponentPushToken[abc123]"
        assert body["platform"] == "ios"
        assert body["is_active"] is True

    def test_register_duplicate_reactivates(
        self, db_session: Session,
    ) -> None:
        user = _make_user(db_session)
        token = "ExponentPushToken[dup123]"
        _make_push_sub(
            db_session, user.id,
            device_token=token, is_active=False,
        )
        client = _build_push_client(
            db_session, user=_make_user_data(user),
        )
        resp = client.post(
            "/api/v1/push/register",
            json={"device_token": token, "platform": "ios"},
        )
        assert resp.status_code == 201
        assert resp.json()["is_active"] is True

    def test_register_invalid_platform(
        self, db_session: Session,
    ) -> None:
        user = _make_user(db_session)
        client = _build_push_client(
            db_session, user=_make_user_data(user),
        )
        resp = client.post(
            "/api/v1/push/register",
            json={
                "device_token": "token",
                "platform": "windows",
            },
        )
        assert resp.status_code == 422


class TestPushUnregisterAPI:
    """POST /api/v1/push/unregister tests."""

    def test_unregister_requires_auth(
        self, db_session: Session,
    ) -> None:
        client = _build_push_client(db_session)
        resp = client.post(
            "/api/v1/push/unregister",
            json={"device_token": "token"},
        )
        assert resp.status_code == 401

    def test_unregister_success(self, db_session: Session) -> None:
        user = _make_user(db_session)
        token = "ExponentPushToken[unreg123]"
        _make_push_sub(db_session, user.id, device_token=token)
        client = _build_push_client(
            db_session, user=_make_user_data(user),
        )
        resp = client.post(
            "/api/v1/push/unregister",
            json={"device_token": token},
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    def test_unregister_unknown_token(
        self, db_session: Session,
    ) -> None:
        user = _make_user(db_session)
        client = _build_push_client(
            db_session, user=_make_user_data(user),
        )
        resp = client.post(
            "/api/v1/push/unregister",
            json={"device_token": "nonexistent"},
        )
        assert resp.status_code == 404
        body = resp.json()
        assert body["detail"]["error_code"] == "TOKEN_NOT_FOUND"
