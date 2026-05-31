"""Tests for BILL-003: Usage quotas — costs, history, daily reset, rate limits.

Covers: get_monthly_cost, get_usage_history, daily reset behaviour,
per-plan rate limiting configuration.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from src.backend.models.subscription import Subscription
from src.backend.models.usage import DailyUsage
from src.backend.models.user import User


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


def _make_usage(
    user_id: uuid.UUID, **overrides: object
) -> DailyUsage:
    """Build a DailyUsage with sensible defaults."""
    defaults: dict[str, object] = {
        "user_id": user_id,
        "usage_date": date.today(),
        "opportunities_found": 0,
        "api_calls": 0,
        "email_sent": 0,
        "push_sent": 0,
        "drafts_regenerated": 0,
        "stripe_cost": Decimal("0"),
        "ai_cost": Decimal("0"),
        "search_cost": Decimal("0"),
    }
    defaults.update(overrides)
    return DailyUsage(**defaults)


def _setup_user_with_plan(
    db_session: Session,
    plan_id: str = "free",
) -> User:
    """Create a user with a subscription on the given plan."""
    user = _make_user()
    db_session.add(user)
    db_session.commit()
    sub = _make_subscription(user.id, plan_id=plan_id)
    db_session.add(sub)
    db_session.commit()
    return user


class TestGetMonthlyCost:
    """UsageService.get_monthly_cost returns cost breakdown."""

    def test_returns_zero_cost_with_no_usage(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = _setup_user_with_plan(db_session, "free")
        svc = UsageService(session=db_session)

        result = svc.get_monthly_cost(user_id=user.id)

        assert result.total == Decimal("0")
        assert result.stripe_cost == Decimal("0")

    def test_sums_costs_across_days(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = _setup_user_with_plan(db_session, "pro")
        today = date.today()

        for i in range(3):
            usage = _make_usage(
                user.id,
                usage_date=today - timedelta(days=i),
                ai_cost=Decimal("1.50"),
                search_cost=Decimal("0.25"),
            )
            db_session.add(usage)
        db_session.commit()

        svc = UsageService(session=db_session)
        result = svc.get_monthly_cost(user_id=user.id)

        assert result.ai_cost == Decimal("4.50")
        assert result.search_cost == Decimal("0.75")


class TestDailyReset:
    """Usage resets daily — separate rows per date."""

    def test_different_dates_have_separate_rows(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = _setup_user_with_plan(db_session, "pro")
        yesterday = date.today() - timedelta(days=1)

        usage_yesterday = _make_usage(
            user.id,
            usage_date=yesterday,
            opportunities_found=50,
        )
        db_session.add(usage_yesterday)
        db_session.commit()

        svc = UsageService(session=db_session)
        svc.record_scan(user_id=user.id, opportunities_count=10)

        result = svc.get_usage_today(user_id=user.id)
        assert result.opportunities_found == 10

    def test_quota_only_checks_today(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = _setup_user_with_plan(db_session, "free")
        yesterday = date.today() - timedelta(days=1)

        usage_yesterday = _make_usage(
            user.id,
            usage_date=yesterday,
            opportunities_found=100,
        )
        db_session.add(usage_yesterday)
        db_session.commit()

        svc = UsageService(session=db_session)
        result = svc.is_quota_exceeded(user_id=user.id)

        assert result.exceeded is False
        assert result.current == 0


class TestHistoricalUsage:
    """Historical usage is queryable for last 30 days."""

    def test_get_usage_history(self, db_session: Session) -> None:
        from src.backend.services.usage_service import UsageService

        user = _setup_user_with_plan(db_session, "pro")
        today = date.today()

        for i in range(5):
            usage = _make_usage(
                user.id,
                usage_date=today - timedelta(days=i),
                opportunities_found=i * 10,
            )
            db_session.add(usage)
        db_session.commit()

        svc = UsageService(session=db_session)
        history = svc.get_usage_history(
            user_id=user.id, days=30
        )

        assert len(history) == 5
        assert history[0].date >= history[-1].date


class TestPlanRateLimits:
    """Per-plan API rate limiting configuration."""

    def test_free_plan_rate_limit(self) -> None:
        from src.backend.services.usage_service import PLAN_QUOTAS

        assert PLAN_QUOTAS["free"].api_calls_per_minute == 10

    def test_pro_plan_rate_limit(self) -> None:
        from src.backend.services.usage_service import PLAN_QUOTAS

        assert PLAN_QUOTAS["pro"].api_calls_per_minute == 100

    def test_premium_plan_rate_limit(self) -> None:
        from src.backend.services.usage_service import PLAN_QUOTAS

        assert PLAN_QUOTAS["premium"].api_calls_per_minute == 1000

    def test_get_rate_limit_for_user(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = _setup_user_with_plan(db_session, "pro")
        svc = UsageService(session=db_session)

        limit = svc.get_rate_limit(user_id=user.id)
        assert limit == 100
