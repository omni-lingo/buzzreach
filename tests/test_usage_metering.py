"""Tests for BILL-003: Usage metering — recording and quota enforcement.

Covers: record_scan, record_api_call, is_quota_exceeded,
get_usage_today, record_cost.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from src.backend.models.usage import DailyUsage
from tests.conftest import make_subscription, make_user, setup_user_with_plan


class TestRecordScan:
    """UsageService.record_scan increments daily opportunity count."""

    def test_creates_usage_row_on_first_scan(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "pro")
        svc = UsageService(session=db_session)

        svc.record_scan(user_id=user.id, opportunities_count=3)

        row = (
            db_session.query(DailyUsage)
            .filter_by(user_id=user.id)
            .first()
        )
        assert row is not None
        assert row.opportunities_found == 3

    def test_increments_existing_usage_row(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "pro")
        svc = UsageService(session=db_session)

        svc.record_scan(user_id=user.id, opportunities_count=5)
        svc.record_scan(user_id=user.id, opportunities_count=3)

        row = (
            db_session.query(DailyUsage)
            .filter_by(user_id=user.id)
            .first()
        )
        assert row is not None
        assert row.opportunities_found == 8


class TestRecordApiCall:
    """UsageService.record_api_call increments API call count."""

    def test_increments_api_calls(self, db_session: Session) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "free")
        svc = UsageService(session=db_session)

        svc.record_api_call(user_id=user.id)
        svc.record_api_call(user_id=user.id)

        row = (
            db_session.query(DailyUsage)
            .filter_by(user_id=user.id)
            .first()
        )
        assert row is not None
        assert row.api_calls == 2


class TestRecordCost:
    """UsageService.record_cost tracks cost components."""

    def test_record_ai_and_search_cost(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "pro")
        svc = UsageService(session=db_session)

        svc.record_cost(
            user_id=user.id,
            ai_cost=Decimal("0.05"),
            search_cost=Decimal("0.01"),
        )

        result = svc.get_usage_today(user_id=user.id)
        assert result.cost_estimate == Decimal("0.06")

    def test_record_all_cost_types(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "pro")
        svc = UsageService(session=db_session)

        svc.record_cost(
            user_id=user.id,
            ai_cost=Decimal("0.10"),
            search_cost=Decimal("0.05"),
            stripe_cost=Decimal("0.03"),
        )

        result = svc.get_usage_today(user_id=user.id)
        assert result.cost_estimate == Decimal("0.18")

    def test_costs_accumulate_across_calls(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "pro")
        svc = UsageService(session=db_session)

        svc.record_cost(user_id=user.id, ai_cost=Decimal("0.10"))
        svc.record_cost(user_id=user.id, ai_cost=Decimal("0.20"))

        result = svc.get_usage_today(user_id=user.id)
        assert result.cost_estimate == Decimal("0.30")


class TestIsQuotaExceeded:
    """UsageService.is_quota_exceeded checks plan limits."""

    def test_free_plan_not_exceeded(self, db_session: Session) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "free")
        svc = UsageService(session=db_session)
        svc.record_scan(user_id=user.id, opportunities_count=3)

        result = svc.is_quota_exceeded(user_id=user.id)
        assert result.exceeded is False
        assert result.current == 3
        assert result.limit == 5

    def test_free_plan_exceeded_at_limit(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "free")
        svc = UsageService(session=db_session)
        svc.record_scan(user_id=user.id, opportunities_count=5)

        result = svc.is_quota_exceeded(user_id=user.id)
        assert result.exceeded is True
        assert result.upgrade_message is not None
        assert "Pro" in result.upgrade_message

    def test_pro_plan_limit_100(self, db_session: Session) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "pro")
        svc = UsageService(session=db_session)
        svc.record_scan(user_id=user.id, opportunities_count=99)

        result = svc.is_quota_exceeded(user_id=user.id)
        assert result.exceeded is False
        assert result.limit == 100

    def test_pro_plan_exceeded(self, db_session: Session) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "pro")
        svc = UsageService(session=db_session)
        svc.record_scan(user_id=user.id, opportunities_count=100)

        result = svc.is_quota_exceeded(user_id=user.id)
        assert result.exceeded is True
        assert "Premium" in (result.upgrade_message or "")

    def test_premium_never_exceeded(self, db_session: Session) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "premium")
        svc = UsageService(session=db_session)
        svc.record_scan(user_id=user.id, opportunities_count=9999)

        result = svc.is_quota_exceeded(user_id=user.id)
        assert result.exceeded is False
        assert result.upgrade_message is None

    def test_no_subscription_uses_free(self, db_session: Session) -> None:
        from src.backend.services.usage_service import UsageService

        user = make_user()
        db_session.add(user)
        db_session.commit()

        svc = UsageService(session=db_session)
        svc.record_scan(user_id=user.id, opportunities_count=5)
        result = svc.is_quota_exceeded(user_id=user.id)

        assert result.exceeded is True
        assert result.plan_id == "free"

    def test_canceled_sub_uses_free(self, db_session: Session) -> None:
        from src.backend.services.usage_service import UsageService

        user = make_user()
        db_session.add(user)
        db_session.commit()
        sub = make_subscription(user.id, plan_id="pro", status="canceled")
        db_session.add(sub)
        db_session.commit()

        svc = UsageService(session=db_session)
        svc.record_scan(user_id=user.id, opportunities_count=5)
        result = svc.is_quota_exceeded(user_id=user.id)

        assert result.exceeded is True
        assert result.plan_id == "free"


class TestGetUsageToday:
    """UsageService.get_usage_today returns current day snapshot."""

    def test_returns_zeros_when_no_usage(self, db_session: Session) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "free")
        svc = UsageService(session=db_session)
        result = svc.get_usage_today(user_id=user.id)

        assert result.opportunities_found == 0
        assert result.api_calls == 0
        assert result.cost_estimate == Decimal("0")

    def test_returns_recorded_usage(self, db_session: Session) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "pro")
        svc = UsageService(session=db_session)
        svc.record_scan(user_id=user.id, opportunities_count=10)
        svc.record_api_call(user_id=user.id)

        result = svc.get_usage_today(user_id=user.id)
        assert result.opportunities_found == 10
        assert result.api_calls == 1

    def test_snapshot_has_user_id_and_date(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "free")
        svc = UsageService(session=db_session)
        result = svc.get_usage_today(user_id=user.id)

        assert result.user_id == user.id
        assert result.date == date.today()
