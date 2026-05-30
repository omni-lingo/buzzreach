"""Tests for BILL-002: SubscriptionService — plan queries & expiration.

Covers: get_user_plan, expire_past_due_subscriptions.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from contracts.billing.subscription import SubscriptionStatus
from src.backend.db.base import Base
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


class TestGetUserPlan:
    """SubscriptionService.get_user_plan returns active plan or free."""

    def test_returns_free_when_no_subscription(
        self, db_session: Session
    ) -> None:
        from src.backend.services.subscription_service import (
            SubscriptionService,
        )

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        svc = SubscriptionService(session=db_session, stripe_api_key="sk_test")
        result = svc.get_user_plan(user_id=user.id)

        assert result.plan_id == "free"
        assert result.status == SubscriptionStatus.NONE
        assert result.entitlements.opportunities_per_day == 5

    def test_returns_active_pro_plan(self, db_session: Session) -> None:
        from src.backend.services.subscription_service import (
            SubscriptionService,
        )

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        now = datetime.now(UTC)
        sub = _make_subscription(
            user_id=user.id,
            plan_id="pro",
            status="active",
            current_period_end=now + timedelta(days=30),
            auto_renew=True,
        )
        db_session.add(sub)
        db_session.commit()

        svc = SubscriptionService(session=db_session, stripe_api_key="sk_test")
        result = svc.get_user_plan(user_id=user.id)

        assert result.plan_id == "pro"
        assert result.status == SubscriptionStatus.ACTIVE
        assert result.entitlements.opportunities_per_day == 100
        assert result.auto_renew is True

    def test_canceled_plan_still_returned(
        self, db_session: Session
    ) -> None:
        from src.backend.services.subscription_service import (
            SubscriptionService,
        )

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        sub = _make_subscription(
            user_id=user.id, plan_id="pro", status="canceled"
        )
        db_session.add(sub)
        db_session.commit()

        svc = SubscriptionService(session=db_session, stripe_api_key="sk_test")
        result = svc.get_user_plan(user_id=user.id)

        assert result.plan_id == "pro"
        assert result.status == SubscriptionStatus.CANCELED


class TestExpirePastDue:
    """Expired subscriptions revert to free plan automatically."""

    def test_past_due_reverted_to_free(self, db_session: Session) -> None:
        from src.backend.services.subscription_service import (
            SubscriptionService,
        )

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        past = datetime.now(UTC) - timedelta(days=1)
        sub = _make_subscription(
            user_id=user.id,
            plan_id="pro",
            status="past_due",
            current_period_end=past,
        )
        db_session.add(sub)
        db_session.commit()

        svc = SubscriptionService(session=db_session, stripe_api_key="sk_test")
        count = svc.expire_past_due_subscriptions()

        assert count == 1
        db_session.refresh(sub)
        assert sub.plan_id == "free"
        assert sub.status == "canceled"

    def test_active_sub_not_expired(self, db_session: Session) -> None:
        from src.backend.services.subscription_service import (
            SubscriptionService,
        )

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        future = datetime.now(UTC) + timedelta(days=30)
        sub = _make_subscription(
            user_id=user.id,
            plan_id="pro",
            status="active",
            current_period_end=future,
        )
        db_session.add(sub)
        db_session.commit()

        svc = SubscriptionService(session=db_session, stripe_api_key="sk_test")
        count = svc.expire_past_due_subscriptions()

        assert count == 0
        db_session.refresh(sub)
        assert sub.plan_id == "pro"
        assert sub.status == "active"
