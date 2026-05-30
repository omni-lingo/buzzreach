"""Tests for BILL-002: Plan upgrade and downgrade operations.

Covers: upgrade_plan, downgrade_plan, Stripe checkout creation,
proration, and error cases.
All Stripe API calls are mocked — no live API calls during CI.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.backend.db.base import Base
from src.backend.errors import AppError
from src.backend.models.stripe_customer import StripeCustomer
from src.backend.models.subscription import Subscription
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


def _make_stripe_customer(
    user_id: uuid.UUID, **overrides: object
) -> StripeCustomer:
    """Build a StripeCustomer with sensible defaults."""
    defaults: dict[str, object] = {
        "user_id": user_id,
        "stripe_customer_id": f"cus_{uuid.uuid4().hex[:12]}",
    }
    defaults.update(overrides)
    return StripeCustomer(**defaults)


def _make_subscription(
    user_id: uuid.UUID, **overrides: object
) -> Subscription:
    """Build a Subscription with sensible defaults."""
    defaults: dict[str, object] = {
        "user_id": user_id,
        "plan_id": "free",
        "status": "active",
    }
    defaults.update(overrides)
    return Subscription(**defaults)


class TestUpgradePlan:
    """SubscriptionService.upgrade_plan triggers Stripe checkout."""

    @patch("src.backend.services.subscription_service.stripe")
    def test_creates_checkout(
        self, mock_stripe: MagicMock, db_session: Session
    ) -> None:
        from src.backend.services.subscription_service import (
            SubscriptionService,
        )

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        sc = _make_stripe_customer(user.id)
        db_session.add(sc)
        db_session.commit()

        mock_session = MagicMock(url="https://checkout.stripe.com/sess_up")
        mock_stripe.checkout.Session.create.return_value = mock_session

        svc = SubscriptionService(session=db_session, stripe_api_key="sk_test")
        url = svc.upgrade_plan(user_id=user.id, new_plan_id="pro")

        assert url == "https://checkout.stripe.com/sess_up"
        mock_stripe.checkout.Session.create.assert_called_once()

    def test_same_plan_raises(self, db_session: Session) -> None:
        from src.backend.services.subscription_service import (
            SubscriptionService,
        )

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        sub = _make_subscription(
            user_id=user.id, plan_id="pro", status="active"
        )
        db_session.add(sub)
        sc = _make_stripe_customer(user.id)
        db_session.add(sc)
        db_session.commit()

        svc = SubscriptionService(session=db_session, stripe_api_key="sk_test")
        with pytest.raises(AppError) as exc_info:
            svc.upgrade_plan(user_id=user.id, new_plan_id="pro")
        assert exc_info.value.code == "ALREADY_ON_PLAN"

    def test_invalid_plan_raises(self, db_session: Session) -> None:
        from src.backend.services.subscription_service import (
            SubscriptionService,
        )

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        svc = SubscriptionService(session=db_session, stripe_api_key="sk_test")
        with pytest.raises(AppError) as exc_info:
            svc.upgrade_plan(user_id=user.id, new_plan_id="nonexistent")
        assert exc_info.value.code == "INVALID_PLAN"

    def test_requires_stripe_customer(self, db_session: Session) -> None:
        from src.backend.services.subscription_service import (
            SubscriptionService,
        )

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        svc = SubscriptionService(session=db_session, stripe_api_key="sk_test")
        with pytest.raises(AppError) as exc_info:
            svc.upgrade_plan(user_id=user.id, new_plan_id="pro")
        assert exc_info.value.code == "CUSTOMER_NOT_FOUND"


class TestDowngradePlan:
    """SubscriptionService.downgrade_plan handles proration via Stripe."""

    @patch("src.backend.services.subscription_service.stripe")
    def test_modifies_stripe_subscription(
        self, mock_stripe: MagicMock, db_session: Session
    ) -> None:
        from src.backend.services.subscription_service import (
            SubscriptionService,
        )

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        sub = _make_subscription(
            user_id=user.id,
            plan_id="premium",
            status="active",
            stripe_subscription_id="sub_existing",
        )
        db_session.add(sub)
        sc = _make_stripe_customer(
            user.id, stripe_subscription_id="sub_existing"
        )
        db_session.add(sc)
        db_session.commit()

        mock_sub = MagicMock()
        mock_sub.items.data = [MagicMock(id="si_item1")]
        mock_stripe.Subscription.retrieve.return_value = mock_sub
        mock_stripe.Subscription.modify.return_value = mock_sub

        svc = SubscriptionService(session=db_session, stripe_api_key="sk_test")
        svc.downgrade_plan(user_id=user.id, new_plan_id="pro")

        mock_stripe.Subscription.modify.assert_called_once()
        call_kwargs = mock_stripe.Subscription.modify.call_args
        assert call_kwargs[1]["proration_behavior"] == "create_prorations"

    def test_to_free_cancels(self, db_session: Session) -> None:
        from src.backend.services.subscription_service import (
            SubscriptionService,
        )

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        sub = _make_subscription(
            user_id=user.id,
            plan_id="pro",
            status="active",
            stripe_subscription_id="sub_cancel",
        )
        db_session.add(sub)
        sc = _make_stripe_customer(
            user.id, stripe_subscription_id="sub_cancel"
        )
        db_session.add(sc)
        db_session.commit()

        svc = SubscriptionService(session=db_session, stripe_api_key="sk_test")
        with patch(
            "src.backend.services.subscription_service.stripe"
        ) as mock_stripe:
            svc.downgrade_plan(user_id=user.id, new_plan_id="free")
            mock_stripe.Subscription.cancel.assert_called_once_with(
                "sub_cancel"
            )

    def test_without_active_sub_raises(self, db_session: Session) -> None:
        from src.backend.services.subscription_service import (
            SubscriptionService,
        )

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        svc = SubscriptionService(session=db_session, stripe_api_key="sk_test")
        with pytest.raises(AppError) as exc_info:
            svc.downgrade_plan(user_id=user.id, new_plan_id="free")
        assert exc_info.value.code == "NO_ACTIVE_SUBSCRIPTION"
