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
    UsageSnapshot,
)
from src.backend.models.subscription import Subscription
from src.backend.models.usage import DailyUsage

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
        row = self._get_or_create_today(user_id)
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
        row = self._get_or_create_today(user_id)
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
        row = self._get_or_create_today(user_id)
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

    def is_quota_exceeded(self, user_id: UUID) -> QuotaStatus:
        """Check if the user has hit their daily opportunity limit."""
        plan_id = self._resolve_plan_id(user_id)
        quota = PLAN_QUOTAS.get(plan_id, PLAN_QUOTAS["free"])
        row = self._get_today(user_id)
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
        row = self._get_today(user_id)
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

        return self._row_to_snapshot(row)

    def get_monthly_cost(self, user_id: UUID) -> MonthlyCost:
        """Return estimated cost breakdown for the current month."""
        today = date.today()
        month_start = today.replace(day=1)
        rows = self._get_usage_range(user_id, month_start, today)

        totals = self._sum_costs(rows)

        sub = self._get_subscription(user_id)
        period_start = sub.current_period_start if sub else None
        period_end = sub.current_period_end if sub else None

        return MonthlyCost(
            user_id=user_id,
            stripe_cost=totals["stripe"],
            ai_cost=totals["ai"],
            search_cost=totals["search"],
            total=totals["stripe"] + totals["ai"] + totals["search"],
            period_start=period_start,
            period_end=period_end,
        )

    def get_usage_history(
        self, user_id: UUID, days: int = _DEFAULT_HISTORY_DAYS
    ) -> list[UsageSnapshot]:
        """Return usage snapshots for the last N days, newest first."""
        today = date.today()
        start = today - timedelta(days=days)
        rows = self._get_usage_range(user_id, start, today)
        rows.sort(key=lambda r: r.usage_date, reverse=True)
        return [self._row_to_snapshot(r) for r in rows]

    def get_rate_limit(self, user_id: UUID) -> int:
        """Return the API calls per minute limit for the user's plan."""
        plan_id = self._resolve_plan_id(user_id)
        quota = PLAN_QUOTAS.get(plan_id, PLAN_QUOTAS["free"])
        return quota.api_calls_per_minute

    # --- Private helpers ---

    def _get_or_create_today(self, user_id: UUID) -> DailyUsage:
        """Return today's usage row, creating it if absent."""
        today = date.today()
        row = (
            self._session.query(DailyUsage)
            .filter_by(user_id=user_id, usage_date=today)
            .first()
        )
        if row is not None:
            return row

        row = DailyUsage(user_id=user_id, usage_date=today)
        self._session.add(row)
        self._session.flush()
        return row

    def _get_today(self, user_id: UUID) -> DailyUsage | None:
        """Return today's usage row or None."""
        return (
            self._session.query(DailyUsage)
            .filter_by(user_id=user_id, usage_date=date.today())
            .first()
        )

    def _get_usage_range(
        self, user_id: UUID, start: date, end: date
    ) -> list[DailyUsage]:
        """Return usage rows in [start, end] inclusive."""
        return (
            self._session.query(DailyUsage)
            .filter(
                DailyUsage.user_id == user_id,
                DailyUsage.usage_date >= start,
                DailyUsage.usage_date <= end,
            )
            .all()
        )

    def _get_subscription(
        self, user_id: UUID
    ) -> Subscription | None:
        """Look up the user's subscription row."""
        return (
            self._session.query(Subscription)
            .filter_by(user_id=user_id)
            .first()
        )

    def _resolve_plan_id(self, user_id: UUID) -> str:
        """Return the user's active plan ID, defaulting to free."""
        sub = self._get_subscription(user_id)
        if sub is None or sub.status not in ("active", "past_due"):
            return "free"
        return sub.plan_id

    @staticmethod
    def _row_to_snapshot(row: DailyUsage) -> UsageSnapshot:
        """Convert a DailyUsage row to a UsageSnapshot contract."""
        cost = row.stripe_cost + row.ai_cost + row.search_cost
        return UsageSnapshot(
            user_id=row.user_id,
            date=row.usage_date,
            opportunities_found=row.opportunities_found,
            api_calls=row.api_calls,
            email_sent=row.email_sent,
            push_sent=row.push_sent,
            drafts_regenerated=row.drafts_regenerated,
            cost_estimate=cost,
        )

    @staticmethod
    def _sum_costs(
        rows: list[DailyUsage],
    ) -> dict[str, Decimal]:
        """Sum cost components across multiple usage rows."""
        totals: dict[str, Decimal] = {
            "stripe": Decimal("0"),
            "ai": Decimal("0"),
            "search": Decimal("0"),
        }
        for row in rows:
            totals["stripe"] += row.stripe_cost
            totals["ai"] += row.ai_cost
            totals["search"] += row.search_cost
        return totals
