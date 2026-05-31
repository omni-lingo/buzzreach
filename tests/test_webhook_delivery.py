"""Tests for webhook retry, auto-disable, and log trimming (EXT-003).

Covers: 3-attempt retry with backoff, auto-disable after 10
consecutive failures, delivery log capped at 100.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from contracts.extensions.webhook import WebhookEventType
from src.backend.db.base import Base
from src.backend.models.webhook import Webhook
from src.backend.models.webhook_log import WebhookDeliveryLog
from src.backend.services.webhook_service import send_webhook
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


def _setup_user_and_webhook(
    db_session: Session,
) -> Webhook:
    """Insert user + webhook, return the webhook."""
    user = make_user()
    db_session.add(user)
    db_session.commit()
    wh = _make_webhook(user.id)
    db_session.add(wh)
    db_session.commit()
    return wh


class TestRetryLogic:
    """Verify retry happens 3 times on failure."""

    @patch("src.backend.services.webhook_service._http_post")
    @patch("src.backend.services.webhook_service._backoff_sleep")
    def test_retries_three_times_on_failure(
        self, mock_sleep: MagicMock,
        mock_post: MagicMock, db_session: Session,
    ) -> None:
        mock_post.side_effect = Exception("connection refused")
        wh = _setup_user_and_webhook(db_session)

        send_webhook(
            session=db_session, webhook=wh,
            event_type="opportunity_created", data={"id": "opp-1"},
        )

        assert mock_post.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("src.backend.services.webhook_service._http_post")
    @patch("src.backend.services.webhook_service._backoff_sleep")
    def test_logs_failure_after_exhausted_retries(
        self, mock_sleep: MagicMock,
        mock_post: MagicMock, db_session: Session,
    ) -> None:
        mock_post.side_effect = Exception("timeout")
        wh = _setup_user_and_webhook(db_session)

        send_webhook(
            session=db_session, webhook=wh,
            event_type="opportunity_created", data={"id": "opp-1"},
        )

        logs = db_session.query(WebhookDeliveryLog).all()
        assert len(logs) == 1
        assert logs[0].success is False

    @patch("src.backend.services.webhook_service._http_post")
    @patch("src.backend.services.webhook_service._backoff_sleep")
    def test_succeeds_on_second_attempt(
        self, mock_sleep: MagicMock,
        mock_post: MagicMock, db_session: Session,
    ) -> None:
        mock_post.side_effect = [Exception("fail"), (200, "OK")]
        wh = _setup_user_and_webhook(db_session)

        send_webhook(
            session=db_session, webhook=wh,
            event_type="opportunity_created", data={"id": "opp-1"},
        )

        assert mock_post.call_count == 2
        logs = db_session.query(WebhookDeliveryLog).all()
        assert len(logs) == 1
        assert logs[0].success is True


class TestAutoDisable:
    """Webhook disabled after 10 consecutive failures."""

    @patch("src.backend.services.webhook_service._http_post")
    @patch("src.backend.services.webhook_service._backoff_sleep")
    def test_disables_after_ten_consecutive_failures(
        self, mock_sleep: MagicMock,
        mock_post: MagicMock, db_session: Session,
    ) -> None:
        mock_post.side_effect = Exception("down")
        wh = _setup_user_and_webhook(db_session)

        for _ in range(10):
            send_webhook(
                session=db_session, webhook=wh,
                event_type="opportunity_created",
                data={"id": "opp-x"},
            )

        db_session.refresh(wh)
        assert wh.active is False
        assert wh.consecutive_failures >= 10


class TestDeliveryLogs:
    """Delivery logs show last 100 events."""

    @patch("src.backend.services.webhook_service._http_post")
    def test_trims_logs_to_100(
        self, mock_post: MagicMock, db_session: Session,
    ) -> None:
        mock_post.return_value = (200, "OK")
        wh = _setup_user_and_webhook(db_session)

        for i in range(105):
            send_webhook(
                session=db_session, webhook=wh,
                event_type="opportunity_created",
                data={"id": f"opp-{i}"},
            )

        logs = (
            db_session.query(WebhookDeliveryLog)
            .filter(WebhookDeliveryLog.webhook_id == wh.id)
            .all()
        )
        assert len(logs) <= 100
