"""Tests for BILL-001: StripeService business logic.

Covers: create_customer, create_checkout_session, cancel_subscription,
get_current_subscription, retry logic, and secret leak prevention.
All Stripe API calls are mocked — no live API calls during CI.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from contracts.billing.subscription import SubscriptionStatus
from src.backend.db.base import Base
from src.backend.errors import AppError
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


def _make_user(**overrides: object) -> User:
    """Build a User with sensible defaults."""
    defaults: dict[str, object] = {
        "username": f"user_{uuid.uuid4().hex[:8]}",
        "email": f"{uuid.uuid4().hex[:8]}@test.com",
        "password_hash": "hashed_pw_placeholder",
        "api_key": f"bz_{uuid.uuid4().hex[:24]}",
    }
    defaults.update(overrides)
    return User(**defaults)


class TestCreateCustomer:
    """StripeService.create_customer creates Stripe customer and DB record."""

    @patch("src.backend.services.stripe_service.stripe")
    def test_creates_customer_and_stores_id(
        self, mock_stripe: MagicMock, db_session: Session
    ) -> None:
        from src.backend.services.stripe_service import StripeService

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        mock_stripe.Customer.create.return_value = MagicMock(id="cus_new_abc")

        svc = StripeService(api_key="sk_test_fake", session=db_session)
        result = svc.create_customer(user_id=user.id, email=user.email)

        assert result == "cus_new_abc"
        sc = db_session.query(StripeCustomer).filter_by(user_id=user.id).first()
        assert sc is not None
        assert sc.stripe_customer_id == "cus_new_abc"

    @patch("src.backend.services.stripe_service.stripe")
    def test_returns_existing_customer_id(
        self, mock_stripe: MagicMock, db_session: Session
    ) -> None:
        from src.backend.services.stripe_service import StripeService

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        sc = StripeCustomer(user_id=user.id, stripe_customer_id="cus_existing")
        db_session.add(sc)
        db_session.commit()

        svc = StripeService(api_key="sk_test_fake", session=db_session)
        result = svc.create_customer(user_id=user.id, email=user.email)

        assert result == "cus_existing"
        mock_stripe.Customer.create.assert_not_called()


class TestCreateCheckoutSession:
    """StripeService.create_checkout_session returns a Stripe session URL."""

    @patch("src.backend.services.stripe_service.stripe")
    def test_returns_session_url(
        self, mock_stripe: MagicMock, db_session: Session
    ) -> None:
        from src.backend.services.stripe_service import StripeService

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        sc = StripeCustomer(user_id=user.id, stripe_customer_id="cus_checkout")
        db_session.add(sc)
        db_session.commit()

        mock_session = MagicMock(url="https://checkout.stripe.com/sess_123")
        mock_stripe.checkout.Session.create.return_value = mock_session

        svc = StripeService(api_key="sk_test_fake", session=db_session)
        url = svc.create_checkout_session(
            user_id=user.id, plan_id="price_pro_monthly"
        )

        assert url == "https://checkout.stripe.com/sess_123"

    @patch("src.backend.services.stripe_service.stripe")
    def test_raises_if_no_customer(
        self, mock_stripe: MagicMock, db_session: Session
    ) -> None:
        from src.backend.services.stripe_service import StripeService

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        svc = StripeService(api_key="sk_test_fake", session=db_session)
        with pytest.raises(AppError) as exc_info:
            svc.create_checkout_session(
                user_id=user.id, plan_id="price_pro"
            )
        assert exc_info.value.code == "CUSTOMER_NOT_FOUND"


class TestCancelSubscription:
    """StripeService.cancel_subscription cancels via Stripe API."""

    @patch("src.backend.services.stripe_service.stripe")
    def test_cancels_active_subscription(
        self, mock_stripe: MagicMock, db_session: Session
    ) -> None:
        from src.backend.services.stripe_service import StripeService

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        sc = StripeCustomer(
            user_id=user.id,
            stripe_customer_id="cus_cancel",
            stripe_subscription_id="sub_active",
            subscription_status="active",
        )
        db_session.add(sc)
        db_session.commit()

        svc = StripeService(api_key="sk_test_fake", session=db_session)
        svc.cancel_subscription(user_id=user.id)

        mock_stripe.Subscription.cancel.assert_called_once_with("sub_active")

    @patch("src.backend.services.stripe_service.stripe")
    def test_raises_if_no_subscription(
        self, mock_stripe: MagicMock, db_session: Session
    ) -> None:
        from src.backend.services.stripe_service import StripeService

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        sc = StripeCustomer(user_id=user.id, stripe_customer_id="cus_nosub")
        db_session.add(sc)
        db_session.commit()

        svc = StripeService(api_key="sk_test_fake", session=db_session)
        with pytest.raises(AppError) as exc_info:
            svc.cancel_subscription(user_id=user.id)
        assert exc_info.value.code == "NO_ACTIVE_SUBSCRIPTION"


class TestGetCurrentSubscription:
    """StripeService.get_current_subscription returns plan metadata."""

    @patch("src.backend.services.stripe_service.stripe")
    def test_returns_active_subscription(
        self, mock_stripe: MagicMock, db_session: Session
    ) -> None:
        from src.backend.services.stripe_service import StripeService

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        now = datetime.now(UTC)
        sc = StripeCustomer(
            user_id=user.id,
            stripe_customer_id="cus_getsub",
            stripe_subscription_id="sub_active",
            plan_id="price_pro",
            subscription_status="active",
            current_period_end=now,
        )
        db_session.add(sc)
        db_session.commit()

        svc = StripeService(api_key="sk_test_fake", session=db_session)
        result = svc.get_current_subscription(user_id=user.id)

        assert result.status == SubscriptionStatus.ACTIVE
        assert result.plan_id == "price_pro"
        assert result.stripe_subscription_id == "sub_active"

    def test_returns_none_status_when_no_customer(
        self, db_session: Session
    ) -> None:
        from src.backend.services.stripe_service import StripeService

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        svc = StripeService(api_key="sk_test_fake", session=db_session)
        result = svc.get_current_subscription(user_id=user.id)

        assert result.status == SubscriptionStatus.NONE


class TestRetryLogic:
    """Stripe calls include exponential backoff retry on transient errors."""

    @patch("src.backend.services.stripe_service.stripe")
    @patch("src.backend.services.stripe_service.time.sleep")
    def test_retries_on_api_connection_error(
        self,
        mock_sleep: MagicMock,
        mock_stripe: MagicMock,
        db_session: Session,
    ) -> None:
        from stripe import APIConnectionError

        from src.backend.services.stripe_service import StripeService

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        mock_stripe.Customer.create.side_effect = [
            APIConnectionError("connection failed"),
            APIConnectionError("connection failed"),
            MagicMock(id="cus_retried"),
        ]

        svc = StripeService(api_key="sk_test_fake", session=db_session)
        result = svc.create_customer(user_id=user.id, email=user.email)

        assert result == "cus_retried"
        assert mock_sleep.call_count == 2


class TestNoSecretsLeaked:
    """API keys must never appear in error messages or logs."""

    @patch("src.backend.services.stripe_service.stripe")
    def test_api_key_not_in_error_message(
        self, mock_stripe: MagicMock, db_session: Session
    ) -> None:
        from stripe import AuthenticationError

        from src.backend.services.stripe_service import StripeService

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        mock_stripe.Customer.create.side_effect = AuthenticationError(
            "Invalid API Key provided: sk_test_****1234"
        )

        svc = StripeService(api_key="sk_test_fake", session=db_session)
        with pytest.raises(Exception) as exc_info:
            svc.create_customer(user_id=user.id, email=user.email)

        assert "sk_test_fake" not in str(exc_info.value)
