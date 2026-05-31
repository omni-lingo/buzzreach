"""Tests for BILL-003: Usage quotas — costs, history, daily reset, rate limits.

Covers: get_monthly_cost, get_usage_history, daily reset behaviour,
per-plan rate limiting configuration.
"""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from tests.conftest import (
    make_subscription,
    make_usage,
    make_user,
    setup_user_with_plan,
)


class TestGetMonthlyCost:
    """UsageService.get_monthly_cost returns cost breakdown."""

    def test_returns_zero_cost_with_no_usage(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "free")
        svc = UsageService(session=db_session)
        result = svc.get_monthly_cost(user_id=user.id)

        assert result.total == Decimal("0")
        assert result.stripe_cost == Decimal("0")

    def test_sums_costs_across_days(self, db_session: Session) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "pro")
        today = date.today()
        for i in range(3):
            usage = make_usage(
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

    def test_total_equals_sum_of_components(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "pro")
        usage = make_usage(
            user.id,
            ai_cost=Decimal("2.00"),
            search_cost=Decimal("1.00"),
            stripe_cost=Decimal("0.50"),
        )
        db_session.add(usage)
        db_session.commit()

        svc = UsageService(session=db_session)
        result = svc.get_monthly_cost(user_id=user.id)
        assert result.total == Decimal("3.50")
        assert result.total == (
            result.ai_cost + result.search_cost + result.stripe_cost
        )

    def test_includes_subscription_period(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = make_user()
        db_session.add(user)
        db_session.commit()

        period_start = datetime(2025, 5, 1, tzinfo=UTC)
        period_end = datetime(2025, 6, 1, tzinfo=UTC)
        sub = make_subscription(
            user.id,
            plan_id="pro",
            current_period_start=period_start,
            current_period_end=period_end,
        )
        db_session.add(sub)
        db_session.commit()

        svc = UsageService(session=db_session)
        result = svc.get_monthly_cost(user_id=user.id)
        assert result.period_start == period_start
        assert result.period_end == period_end


class TestDailyReset:
    """Usage resets daily — separate rows per date."""

    def test_different_dates_have_separate_rows(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "pro")
        yesterday = date.today() - timedelta(days=1)
        db_session.add(make_usage(
            user.id, usage_date=yesterday, opportunities_found=50
        ))
        db_session.commit()

        svc = UsageService(session=db_session)
        svc.record_scan(user_id=user.id, opportunities_count=10)
        result = svc.get_usage_today(user_id=user.id)
        assert result.opportunities_found == 10

    def test_quota_only_checks_today(self, db_session: Session) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "free")
        yesterday = date.today() - timedelta(days=1)
        db_session.add(make_usage(
            user.id, usage_date=yesterday, opportunities_found=100
        ))
        db_session.commit()

        svc = UsageService(session=db_session)
        result = svc.is_quota_exceeded(user_id=user.id)
        assert result.exceeded is False
        assert result.current == 0


class TestHistoricalUsage:
    """Historical usage is queryable for last 30 days."""

    def test_get_usage_history(self, db_session: Session) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "pro")
        today = date.today()
        for i in range(5):
            db_session.add(make_usage(
                user.id,
                usage_date=today - timedelta(days=i),
                opportunities_found=i * 10,
            ))
        db_session.commit()

        svc = UsageService(session=db_session)
        history = svc.get_usage_history(user_id=user.id, days=30)
        assert len(history) == 5
        assert history[0].date >= history[-1].date

    def test_empty_history(self, db_session: Session) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "free")
        svc = UsageService(session=db_session)
        assert svc.get_usage_history(user_id=user.id) == []

    def test_respects_days_parameter(self, db_session: Session) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "pro")
        today = date.today()
        for i in range(10):
            db_session.add(make_usage(
                user.id,
                usage_date=today - timedelta(days=i),
                opportunities_found=i,
            ))
        db_session.commit()

        svc = UsageService(session=db_session)
        history = svc.get_usage_history(user_id=user.id, days=3)
        assert len(history) == 4  # today + 3 days back


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

    def test_get_rate_limit_for_pro(self, db_session: Session) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "pro")
        svc = UsageService(session=db_session)
        assert svc.get_rate_limit(user_id=user.id) == 100

    def test_get_rate_limit_for_free(self, db_session: Session) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "free")
        svc = UsageService(session=db_session)
        assert svc.get_rate_limit(user_id=user.id) == 10

    def test_get_rate_limit_for_premium(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "premium")
        svc = UsageService(session=db_session)
        assert svc.get_rate_limit(user_id=user.id) == 1000
