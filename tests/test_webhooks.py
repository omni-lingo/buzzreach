"""Tests for webhook send, signature, and model (EXT-003).

Covers: HMAC-SHA256 signature, webhook POST delivery,
delivery log creation, model create/delete.
"""

import hashlib
import hmac
import json
import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from contracts.extensions.webhook import WebhookEventType
from src.backend.db.base import Base
from src.backend.models.user import User
from src.backend.models.webhook import Webhook
from src.backend.models.webhook_log import WebhookDeliveryLog
from src.backend.services.webhook_service import (
    compute_signature,
    send_webhook,
)
from tests.conftest import make_user


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


def _make_webhook(
    user_id: uuid.UUID, **overrides: object,
) -> Webhook:
    """Build a Webhook with sensible defaults."""
    defaults: dict[str, object] = {
        "user_id": user_id,
        "url": "https://example.com/hook",
        "event_type": WebhookEventType.OPPORTUNITY_CREATED.value,
        "secret": "test-secret-key",
        "active": True,
    }
    defaults.update(overrides)
    return Webhook(**defaults)


def _setup_user(db_session: Session) -> User:
    """Insert a user into the test DB."""
    user = make_user()
    db_session.add(user)
    db_session.commit()
    return user


class TestComputeSignature:
    """Verify HMAC-SHA256 signature generation."""

    def test_signature_format(self) -> None:
        sig = compute_signature(b'{"test": true}', "my-secret")
        assert sig.startswith("sha256=")

    def test_signature_matches_hmac(self) -> None:
        body = b'{"event": "opportunity_created"}'
        secret = "my-secret"
        sig = compute_signature(body, secret)
        expected = hmac.new(
            secret.encode(), body, hashlib.sha256,
        ).hexdigest()
        assert sig == f"sha256={expected}"

    def test_different_secrets_produce_different_sigs(self) -> None:
        body = b'{"data": 1}'
        sig1 = compute_signature(body, "secret-a")
        sig2 = compute_signature(body, "secret-b")
        assert sig1 != sig2


class TestSendWebhook:
    """Verify webhook POST request is sent correctly."""

    @patch("src.backend.services.webhook_service._http_post")
    def test_sends_post_with_correct_signature(
        self, mock_post: MagicMock, db_session: Session,
    ) -> None:
        mock_post.return_value = (200, "OK")
        user = _setup_user(db_session)
        wh = _make_webhook(user.id)
        db_session.add(wh)
        db_session.commit()

        payload = {"id": "opp-123", "title": "Test"}
        send_webhook(
            session=db_session, webhook=wh,
            event_type="opportunity_created", data=payload,
        )

        mock_post.assert_called_once()
        sent_body = mock_post.call_args[0][1]
        parsed = json.loads(sent_body)
        assert parsed["event"] == "opportunity_created"
        assert parsed["data"]["id"] == "opp-123"
        assert parsed["signature"].startswith("sha256=")

    @patch("src.backend.services.webhook_service._http_post")
    def test_delivery_log_created_on_success(
        self, mock_post: MagicMock, db_session: Session,
    ) -> None:
        mock_post.return_value = (200, "OK")
        user = _setup_user(db_session)
        wh = _make_webhook(user.id)
        db_session.add(wh)
        db_session.commit()

        send_webhook(
            session=db_session, webhook=wh,
            event_type="opportunity_created", data={"id": "opp-1"},
        )

        logs = db_session.query(WebhookDeliveryLog).all()
        assert len(logs) == 1
        assert logs[0].success is True
        assert logs[0].status_code == 200


class TestWebhookModel:
    """Verify webhook ORM model constraints."""

    def test_create_webhook(self, db_session: Session) -> None:
        user = _setup_user(db_session)
        wh = _make_webhook(user.id)
        db_session.add(wh)
        db_session.commit()

        fetched = db_session.get(Webhook, wh.id)
        assert fetched is not None
        assert fetched.url == "https://example.com/hook"
        assert fetched.active is True

    def test_delete_webhook(self, db_session: Session) -> None:
        user = _setup_user(db_session)
        wh = _make_webhook(user.id)
        db_session.add(wh)
        db_session.commit()

        db_session.delete(wh)
        db_session.commit()
        assert db_session.get(Webhook, wh.id) is None
