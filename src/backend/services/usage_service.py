"""Usage metering and quota enforcement service (BILL-003).

Pure business logic — no HTTP concerns. Tracks per-user daily usage,
enforces plan quotas, computes cost estimates, and provides historical
usage queries.

Cross-module contracts:
- Reads Subscription (BILL-002) for plan lookup
- Reads pipeline metrics (PIPE-001) for cost tracking
- Checked by API rate limiting (RATE-001)
- Displayed in FE-001 (settings / usage bar)
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from contracts.billing.usage import (
    MonthlyCost,
    PlanQuota,
    QuotaStatus,
    UsageDisplay,
    UsageSnapshot,
)
from src.backend.services.usage_queries import (
    compute_monthly_cost,
    days_until_renewal,
    format_usage_summary,
    get_or_create_today,
    get_today,
    get_usage_range,
    resolve_plan_id,
    row_to_snapshot,
)

log = logging.getLogger("buzzreach.billing")

# --- Plan quota definitions ---

PLAN_QUOTAS: dict[str, PlanQuota] = {
    "free": PlanQuota(opportunities_per_day=5, api_calls_per_minute=10),
    "pro": PlanQuota(opportunities_per_day=100, api_calls_per_minute=100),
    "premium": PlanQuota(
        opportunities_per_day=10_000, api_calls_per_minute=1000
    ),
}

_UPGRADE_MESSAGES: dict[str, str] = {
    "free": "Upgrade to Pro for 100 opportunities/day",
    "pro": "Upgrade to Premium for unlimited opportunities/day",
}

_DEFAULT_HISTORY_DAYS = 30


class UsageService:
    """Tracks daily usage, enforces quotas, and computes costs."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def record_scan(
        self, user_id: UUID, opportunities_count: int
    ) -> None:
        """Increment daily opportunity count after a scan completes."""
        row = get_or_create_today(self._session, user_id)
        row.opportunities_found += opportunities_count
        self._session.commit()
        log.info(
            "Scan recorded",
            extra={
                "user_id": str(user_id),
                "opportunities": opportunities_count,
                "daily_total": row.opportunities_found,
            },
        )

    def record_api_call(self, user_id: UUID) -> None:
        """Increment daily API call count."""
        row = get_or_create_today(self._session, user_id)
        row.api_calls += 1
        self._session.commit()

    def record_cost(
        self,
        user_id: UUID,
        ai_cost: Decimal = Decimal("0"),
        search_cost: Decimal = Decimal("0"),
        stripe_cost: Decimal = Decimal("0"),
    ) -> None:
        """Add cost components to today's usage row."""
        row = get_or_create_today(self._session, user_id)
        row.ai_cost += ai_cost
        row.search_cost += search_cost
        row.stripe_cost += stripe_cost
        self._session.commit()
        log.info(
            "Cost recorded",
            extra={
                "user_id": str(user_id),
                "ai_cost": str(ai_cost),
                "search_cost": str(search_cost),
            },
        )

    def record_notification(
        self, user_id: UUID, channel: str
    ) -> None:
        """Increment email or push notification count for today."""
        row = get_or_create_today(self._session, user_id)
        if channel == "email":
            row.email_sent += 1
        elif channel == "push":
            row.push_sent += 1
        self._session.commit()
        log.info(
            "Notification recorded",
            extra={"user_id": str(user_id), "channel": channel},
        )

    def record_draft_regeneration(self, user_id: UUID) -> None:
        """Increment daily draft regeneration count."""
        row = get_or_create_today(self._session, user_id)
        row.drafts_regenerated += 1
        self._session.commit()

    def check_and_record_scan(
        self, user_id: UUID, opportunities_count: int
    ) -> QuotaStatus:
        """Pipeline integration: check quota, record only if allowed.

        Returns the QuotaStatus. If exceeded, does NOT record the scan.
        """
        status = self.is_quota_exceeded(user_id)
        if status.exceeded:
            log.info(
                "Scan blocked by quota",
                extra={
                    "user_id": str(user_id),
                    "plan_id": status.plan_id,
                    "current": status.current,
                    "limit": status.limit,
                },
            )
            return status

        self.record_scan(user_id, opportunities_count)
        updated = self.is_quota_exceeded(user_id)
        return QuotaStatus(
            exceeded=False,
            current=updated.current,
            limit=updated.limit,
            plan_id=updated.plan_id,
            upgrade_message=None,
        )

    def is_quota_exceeded(self, user_id: UUID) -> QuotaStatus:
        """Check if the user has hit their daily opportunity limit."""
        plan_id = resolve_plan_id(self._session, user_id)
        quota = PLAN_QUOTAS.get(plan_id, PLAN_QUOTAS["free"])
        row = get_today(self._session, user_id)
        current = row.opportunities_found if row else 0
        exceeded = current >= quota.opportunities_per_day

        upgrade_msg = _UPGRADE_MESSAGES.get(plan_id) if exceeded else None

        return QuotaStatus(
            exceeded=exceeded,
            current=current,
            limit=quota.opportunities_per_day,
            plan_id=plan_id,
            upgrade_message=upgrade_msg,
        )

    def get_usage_today(self, user_id: UUID) -> UsageSnapshot:
        """Return current day's usage snapshot."""
        row = get_today(self._session, user_id)
        today = date.today()

        if row is None:
            return UsageSnapshot(
                user_id=user_id,
                date=today,
                opportunities_found=0,
                api_calls=0,
                email_sent=0,
                push_sent=0,
                drafts_regenerated=0,
                cost_estimate=Decimal("0"),
            )

        return row_to_snapshot(row)

    def get_monthly_cost(self, user_id: UUID) -> MonthlyCost:
        """Return estimated cost breakdown for the current month."""
        return compute_monthly_cost(self._session, user_id)

    def get_usage_history(
        self, user_id: UUID, days: int = _DEFAULT_HISTORY_DAYS
    ) -> list[UsageSnapshot]:
        """Return usage snapshots for the last N days, newest first."""
        today = date.today()
        start = today - timedelta(days=days)
        rows = get_usage_range(self._session, user_id, start, today)
        rows.sort(key=lambda r: r.usage_date, reverse=True)
        return [row_to_snapshot(r) for r in rows]

    def get_rate_limit(self, user_id: UUID) -> int:
        """Return the API calls per minute limit for the user's plan."""
        plan_id = resolve_plan_id(self._session, user_id)
        quota = PLAN_QUOTAS.get(plan_id, PLAN_QUOTAS["free"])
        return quota.api_calls_per_minute

    def get_usage_display(self, user_id: UUID) -> UsageDisplay:
        """Return frontend-facing usage bar data for settings page."""
        plan_id = resolve_plan_id(self._session, user_id)
        quota = PLAN_QUOTAS.get(plan_id, PLAN_QUOTAS["free"])
        row = get_today(self._session, user_id)
        current = row.opportunities_found if row else 0
        limit = quota.opportunities_per_day

        summary = format_usage_summary(current, limit, plan_id)
        monthly = self.get_monthly_cost(user_id)
        renewal_days = days_until_renewal(self._session, user_id)

        return UsageDisplay(
            current=current,
            limit=limit,
            plan_id=plan_id,
            summary=summary,
            estimated_monthly_cost=monthly.total,
            days_until_renewal=renewal_days,
        )
