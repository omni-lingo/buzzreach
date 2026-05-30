"""Tests for BILL-001: Billing webhook handler.

Covers: webhook signature validation, charge.succeeded,
customer.subscription.deleted, invoice.payment_failed events.
All Stripe calls are mocked — no live API calls during CI.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.backend.db.base import Base
from src.backend.models.stripe_customer import StripeCustomer
from src.backend.models.user import User


@pytest.fixture()
def db_session() -> Session:
    """In-memory SQLite session with the buzzreach schema attached."""
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


def _make_customer(
    db_session: Session, user: User, **overrides: object
) -> StripeCustomer:
    """Create and persist a StripeCustomer record."""
    defaults: dict[str, object] = {
        "user_id": user.id,
        "stripe_customer_id": f"cus_{uuid.uuid4().hex[:12]}",
    }
    defaults.update(overrides)
    sc = StripeCustomer(**defaults)
    db_session.add(sc)
    db_session.commit()
    return sc


class TestWebhookSignatureValidation:
    """Webhook handler rejects requests with invalid signatures."""

    @patch("src.backend.api.billing_webhooks.stripe")
    def test_invalid_signature_returns_400(
        self, mock_stripe: MagicMock
    ) -> None:
        from stripe import SignatureVerificationError

        from src.backend.api.billing_webhooks import _verify_webhook_event

        mock_stripe.Webhook.construct_event.side_effect = (
            SignatureVerificationError("bad sig", "sig_header")
        )

        result = _verify_webhook_event(
            payload=b"body",
            sig_header="bad_sig",
            webhook_secret="whsec_test",
        )
        assert result is None

    @patch("src.backend.api.billing_webhooks.stripe")
    def test_valid_signature_returns_event(
        self, mock_stripe: MagicMock
    ) -> None:
        from src.backend.api.billing_webhooks import _verify_webhook_event

        fake_event = MagicMock()
        fake_event.type = "charge.succeeded"
        mock_stripe.Webhook.construct_event.return_value = fake_event

        result = _verify_webhook_event(
            payload=b"body",
            sig_header="valid_sig",
            webhook_secret="whsec_test",
        )
        assert result is not None
        assert result.type == "charge.succeeded"


class TestChargeSucceeded:
    """charge.succeeded webhook marks user as active subscriber."""

    def test_updates_subscription_status(
        self, db_session: Session
    ) -> None:
        from src.backend.api.billing_webhooks import handle_charge_succeeded

        user = _make_user(db_session)
        sc = _make_customer(db_session, user, stripe_customer_id="cus_chg")

        event_data = {
            "customer": "cus_chg",
            "subscription": "sub_new_123",
        }

        handle_charge_succeeded(event_data, db_session)
        db_session.refresh(sc)

        assert sc.subscription_status == "active"
        assert sc.stripe_subscription_id == "sub_new_123"


class TestSubscriptionDeleted:
    """customer.subscription.deleted marks user as past_due."""

    def test_marks_past_due(self, db_session: Session) -> None:
        from src.backend.api.billing_webhooks import (
            handle_subscription_deleted,
        )

        user = _make_user(db_session)
        sc = _make_customer(
            db_session,
            user,
            stripe_customer_id="cus_del",
            stripe_subscription_id="sub_del",
            subscription_status="active",
        )

        event_data = {"customer": "cus_del", "id": "sub_del"}

        handle_subscription_deleted(event_data, db_session)
        db_session.refresh(sc)

        assert sc.subscription_status == "past_due"
        assert sc.stripe_subscription_id is None


class TestInvoicePaymentFailed:
    """invoice.payment_failed logs a warning (notification stub)."""

    def test_logs_payment_failure(self, db_session: Session) -> None:
        from src.backend.api.billing_webhooks import (
            handle_invoice_payment_failed,
        )

        user = _make_user(db_session)
        _make_customer(db_session, user, stripe_customer_id="cus_fail")

        event_data = {
            "customer": "cus_fail",
            "id": "in_fail_123",
            "amount_due": 2000,
        }

        handle_invoice_payment_failed(event_data, db_session)

        sc = (
            db_session.query(StripeCustomer)
            .filter_by(stripe_customer_id="cus_fail")
            .first()
        )
        assert sc is not None
        assert sc.subscription_status == "past_due"


class TestUnknownEventType:
    """Unknown webhook event types are acknowledged but not processed."""

    def test_unknown_event_returns_ok(self) -> None:
        from src.backend.api.billing_webhooks import _route_event

        fake_event = MagicMock()
        fake_event.type = "totally.unknown.event"
        fake_event.data = MagicMock()
        fake_event.data.object = {}

        result = _route_event(fake_event, session=MagicMock())
        assert result == "unhandled"
