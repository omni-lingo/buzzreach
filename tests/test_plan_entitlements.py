"""Tests for BILL-002: Plan entitlements and feature availability.

Covers: is_feature_available per plan, plan definitions correctness,
and canceled-plan fallback to free entitlements.
"""

import uuid

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

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


class TestIsFeatureAvailable:
    """SubscriptionService.is_feature_available checks plan entitlements."""

    def test_free_plan_has_email_delivery(
        self, db_session: Session
    ) -> None:
        from src.backend.services.subscription_service import (
            SubscriptionService,
        )

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        svc = SubscriptionService(session=db_session, stripe_api_key="sk_test")
        assert svc.is_feature_available(user.id, "email_delivery") is True

    def test_free_plan_no_slack_delivery(
        self, db_session: Session
    ) -> None:
        from src.backend.services.subscription_service import (
            SubscriptionService,
        )

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        svc = SubscriptionService(session=db_session, stripe_api_key="sk_test")
        assert svc.is_feature_available(user.id, "slack_delivery") is False

    def test_pro_plan_has_slack_and_filters(
        self, db_session: Session
    ) -> None:
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
        db_session.commit()

        svc = SubscriptionService(session=db_session, stripe_api_key="sk_test")
        assert svc.is_feature_available(user.id, "slack_delivery") is True
        assert svc.is_feature_available(user.id, "advanced_filters") is True

    def test_premium_plan_has_team_members(
        self, db_session: Session
    ) -> None:
        from src.backend.services.subscription_service import (
            SubscriptionService,
        )

        user = _make_user()
        db_session.add(user)
        db_session.commit()

        sub = _make_subscription(
            user_id=user.id, plan_id="premium", status="active"
        )
        db_session.add(sub)
        db_session.commit()

        svc = SubscriptionService(session=db_session, stripe_api_key="sk_test")
        assert svc.is_feature_available(user.id, "team_members") is True

    def test_canceled_plan_uses_free_entitlements(
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
        assert svc.is_feature_available(user.id, "slack_delivery") is False


class TestPlanDefinitions:
    """Plan definitions have correct entitlements."""

    def test_free_plan_5_opps_per_day(self) -> None:
        from src.backend.services.plan_definitions import FREE_PLAN

        assert FREE_PLAN.opportunities_per_day == 5
        assert FREE_PLAN.price_cents == 0
        assert "email_delivery" in FREE_PLAN.features

    def test_pro_plan_100_opps_per_day(self) -> None:
        from src.backend.services.plan_definitions import PRO_PLAN

        assert PRO_PLAN.opportunities_per_day == 100
        assert PRO_PLAN.price_cents == 4900
        assert "slack_delivery" in PRO_PLAN.features
        assert "advanced_filters" in PRO_PLAN.features

    def test_premium_plan_unlimited(self) -> None:
        from src.backend.services.plan_definitions import PREMIUM_PLAN

        assert PREMIUM_PLAN.opportunities_per_day == 10_000
        assert PREMIUM_PLAN.price_cents == 14900
        assert "team_members" in PREMIUM_PLAN.features

    def test_all_plans_registered(self) -> None:
        from src.backend.services.plan_definitions import PLANS

        assert set(PLANS.keys()) == {"free", "pro", "premium"}
