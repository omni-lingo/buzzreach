"""Tests for BILL-003: Pipeline integration and usage display.

Covers: record_notification, record_draft_regeneration,
check_and_record_scan (pipeline quota gate), get_usage_display
(frontend settings / usage bar).
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from src.backend.models.usage import DailyUsage
from tests.conftest import make_subscription, make_user, setup_user_with_plan


class TestRecordNotification:
    """UsageService.record_notification tracks email/push counts."""

    def test_record_email_sent(self, db_session: Session) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "pro")
        svc = UsageService(session=db_session)

        svc.record_notification(user_id=user.id, channel="email")

        row = (
            db_session.query(DailyUsage)
            .filter_by(user_id=user.id)
            .first()
        )
        assert row is not None
        assert row.email_sent == 1

    def test_record_push_sent(self, db_session: Session) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "pro")
        svc = UsageService(session=db_session)

        svc.record_notification(user_id=user.id, channel="push")

        row = (
            db_session.query(DailyUsage)
            .filter_by(user_id=user.id)
            .first()
        )
        assert row is not None
        assert row.push_sent == 1

    def test_multiple_notifications_accumulate(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "pro")
        svc = UsageService(session=db_session)

        svc.record_notification(user_id=user.id, channel="email")
        svc.record_notification(user_id=user.id, channel="email")
        svc.record_notification(user_id=user.id, channel="push")

        row = (
            db_session.query(DailyUsage)
            .filter_by(user_id=user.id)
            .first()
        )
        assert row is not None
        assert row.email_sent == 2
        assert row.push_sent == 1


class TestRecordDraftRegeneration:
    """UsageService.record_draft_regeneration tracks regen count."""

    def test_increments_drafts_regenerated(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "pro")
        svc = UsageService(session=db_session)

        svc.record_draft_regeneration(user_id=user.id)
        svc.record_draft_regeneration(user_id=user.id)

        row = (
            db_session.query(DailyUsage)
            .filter_by(user_id=user.id)
            .first()
        )
        assert row is not None
        assert row.drafts_regenerated == 2


class TestCheckAndRecordScan:
    """Pipeline integration: check quota, then record scan."""

    def test_allowed_when_under_quota(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "pro")
        svc = UsageService(session=db_session)

        result = svc.check_and_record_scan(
            user_id=user.id, opportunities_count=10
        )
        assert result.exceeded is False
        assert result.current == 10

    def test_blocked_when_over_quota(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "free")
        svc = UsageService(session=db_session)
        svc.record_scan(user_id=user.id, opportunities_count=5)

        result = svc.check_and_record_scan(
            user_id=user.id, opportunities_count=3
        )
        assert result.exceeded is True
        assert result.upgrade_message is not None

    def test_does_not_record_when_quota_exceeded(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "free")
        svc = UsageService(session=db_session)
        svc.record_scan(user_id=user.id, opportunities_count=5)

        svc.check_and_record_scan(
            user_id=user.id, opportunities_count=3
        )
        result = svc.get_usage_today(user_id=user.id)
        assert result.opportunities_found == 5


class TestGetUsageDisplay:
    """UsageService.get_usage_display returns frontend-facing data."""

    def test_display_shows_usage_bar_values(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "pro")
        svc = UsageService(session=db_session)
        svc.record_scan(user_id=user.id, opportunities_count=23)

        display = svc.get_usage_display(user_id=user.id)
        assert display.current == 23
        assert display.limit == 100
        assert display.plan_id == "pro"
        assert display.summary == "23/100 opportunities today"

    def test_display_shows_unlimited_for_premium(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "premium")
        svc = UsageService(session=db_session)
        svc.record_scan(user_id=user.id, opportunities_count=500)

        display = svc.get_usage_display(user_id=user.id)
        assert display.current == 500
        assert display.summary == "500 opportunities today (unlimited)"

    def test_display_includes_monthly_cost(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = setup_user_with_plan(db_session, "pro")
        svc = UsageService(session=db_session)
        svc.record_cost(
            user_id=user.id,
            ai_cost=Decimal("2.50"),
            search_cost=Decimal("0.50"),
        )

        display = svc.get_usage_display(user_id=user.id)
        assert display.estimated_monthly_cost == Decimal("3.00")

    def test_display_includes_days_until_renewal(
        self, db_session: Session
    ) -> None:
        from src.backend.services.usage_service import UsageService

        user = make_user()
        db_session.add(user)
        db_session.commit()

        period_end = datetime.now(UTC) + timedelta(days=15)
        sub = make_subscription(
            user.id,
            plan_id="pro",
            current_period_end=period_end,
        )
        db_session.add(sub)
        db_session.commit()

        svc = UsageService(session=db_session)
        display = svc.get_usage_display(user_id=user.id)
        assert display.days_until_renewal is not None
        assert 14 <= display.days_until_renewal <= 16
