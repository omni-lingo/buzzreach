"""Cross-module contract for usage metering data (BILL-003).

Consumed by:
- API-001 (usage display endpoints)
- FE-001 (settings / usage bar)
- PIPE-001 (quota check before scan)
- RATE-001 (per-plan API rate limiting)
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class UsageSnapshot:
    """Current day's usage for a user — returned by get_usage_today."""

    user_id: UUID
    date: date
    opportunities_found: int
    api_calls: int
    email_sent: int
    push_sent: int
    drafts_regenerated: int
    cost_estimate: Decimal


@dataclass(frozen=True)
class QuotaStatus:
    """Whether a user has exceeded their plan quota."""

    exceeded: bool
    current: int
    limit: int
    plan_id: str
    upgrade_message: str | None


@dataclass(frozen=True)
class MonthlyCost:
    """Estimated monthly cost breakdown for a user."""

    user_id: UUID
    stripe_cost: Decimal
    ai_cost: Decimal
    search_cost: Decimal
    total: Decimal
    period_start: datetime | None
    period_end: datetime | None


@dataclass(frozen=True)
class PlanQuota:
    """Quota limits for a subscription plan."""

    opportunities_per_day: int
    api_calls_per_minute: int


@dataclass(frozen=True)
class UsageDisplay:
    """Frontend-facing usage data for settings / usage bar.

    Shows current vs. limit, formatted summary, estimated cost,
    and days until next billing cycle.
    """

    current: int
    limit: int
    plan_id: str
    summary: str
    estimated_monthly_cost: Decimal
    days_until_renewal: int | None
