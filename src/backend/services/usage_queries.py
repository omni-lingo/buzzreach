"""Usage data access helpers for the billing module (BILL-003).

Extracted from usage_service.py to stay within the 300-line file limit.
Pure data access — queries DailyUsage and Subscription rows,
converts between ORM rows and contract DTOs.

Cross-module contracts:
- Reads DailyUsage (BILL-003)
- Reads Subscription (BILL-002)
- Produces UsageSnapshot, MonthlyCost contracts
"""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from contracts.billing.usage import MonthlyCost, UsageSnapshot
from src.backend.models.subscription import Subscription
from src.backend.models.usage import DailyUsage


def get_or_create_today(
    session: Session, user_id: UUID
) -> DailyUsage:
    """Return today's usage row, creating it if absent."""
    today = date.today()
    row = (
        session.query(DailyUsage)
        .filter_by(user_id=user_id, usage_date=today)
        .first()
    )
    if row is not None:
        return row

    row = DailyUsage(user_id=user_id, usage_date=today)
    session.add(row)
    session.flush()
    return row


def get_today(
    session: Session, user_id: UUID
) -> DailyUsage | None:
    """Return today's usage row or None."""
    return (
        session.query(DailyUsage)
        .filter_by(user_id=user_id, usage_date=date.today())
        .first()
    )


def get_usage_range(
    session: Session, user_id: UUID, start: date, end: date
) -> list[DailyUsage]:
    """Return usage rows in [start, end] inclusive."""
    return (
        session.query(DailyUsage)
        .filter(
            DailyUsage.user_id == user_id,
            DailyUsage.usage_date >= start,
            DailyUsage.usage_date <= end,
        )
        .all()
    )


def get_subscription(
    session: Session, user_id: UUID
) -> Subscription | None:
    """Look up the user's subscription row."""
    return (
        session.query(Subscription)
        .filter_by(user_id=user_id)
        .first()
    )


def resolve_plan_id(
    session: Session, user_id: UUID
) -> str:
    """Return the user's active plan ID, defaulting to free."""
    sub = get_subscription(session, user_id)
    if sub is None or sub.status not in ("active", "past_due"):
        return "free"
    return sub.plan_id


def row_to_snapshot(row: DailyUsage) -> UsageSnapshot:
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


def sum_costs(rows: list[DailyUsage]) -> dict[str, Decimal]:
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


def compute_monthly_cost(
    session: Session, user_id: UUID
) -> MonthlyCost:
    """Return estimated cost breakdown for the current month."""
    today = date.today()
    month_start = today.replace(day=1)
    rows = get_usage_range(session, user_id, month_start, today)

    totals = sum_costs(rows)

    sub = get_subscription(session, user_id)
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


def days_until_renewal(
    session: Session, user_id: UUID
) -> int | None:
    """Calculate days until the next billing cycle, or None."""
    sub = get_subscription(session, user_id)
    if sub is None or sub.current_period_end is None:
        return None
    now = datetime.now(UTC)
    delta = sub.current_period_end - now
    return max(0, delta.days)


def format_usage_summary(
    current: int, limit: int, plan_id: str
) -> str:
    """Format the usage bar summary string for the frontend."""
    if plan_id == "premium":
        return f"{current} opportunities today (unlimited)"
    return f"{current}/{limit} opportunities today"
