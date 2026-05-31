"""Dashboard business logic service (DASH-001, L2).

Pure query logic for the dashboard API. No HTTP concerns.
Reads Opportunity, Metric, and AuditLog tables to produce
summary data consumed by the L3 dashboard routes.
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.backend.models.audit_log import AuditLog
from src.backend.models.metric import Metric
from src.backend.models.opportunity import Opportunity, OpportunityStatus

log = logging.getLogger("buzzreach.services.dashboard")

ERROR_ACTIONS = frozenset({
    "pipeline_error",
    "search_error",
    "extraction_error",
    "scoring_error",
    "draft_error",
    "delivery_error",
})


def get_today_start() -> datetime:
    """Return midnight UTC of the current day."""
    return datetime.now(UTC).replace(
        hour=0, minute=0, second=0, microsecond=0,
    )


def count_today_opportunities(session: Session) -> int:
    """Count opportunities created today."""
    today = get_today_start()
    stmt = select(func.count()).select_from(Opportunity).where(
        Opportunity.created_at >= today,
    )
    return session.execute(stmt).scalar_one()


def count_today_acted(session: Session) -> int:
    """Count opportunities acted on today."""
    today = get_today_start()
    stmt = (
        select(func.count())
        .select_from(Opportunity)
        .where(
            Opportunity.created_at >= today,
            Opportunity.status == OpportunityStatus.ACTED,
        )
    )
    return session.execute(stmt).scalar_one()


def sum_today_ai_tokens(session: Session) -> int:
    """Sum all AI token metrics recorded today."""
    today = get_today_start()
    stmt = select(func.coalesce(func.sum(Metric.value), 0.0)).where(
        Metric.timestamp >= today,
        Metric.metric_name.like("ai_%_tokens_%"),
    )
    result = session.execute(stmt).scalar_one()
    return int(result)


def sum_today_cost(session: Session) -> float:
    """Sum all ai_cost_usd metrics recorded today."""
    today = get_today_start()
    stmt = select(func.coalesce(func.sum(Metric.value), 0.0)).where(
        Metric.timestamp >= today,
        Metric.metric_name == "ai_cost_usd",
    )
    return float(session.execute(stmt).scalar_one())


def count_recent_errors(
    session: Session, hours: int = 24,
) -> int:
    """Count error audit log entries in the last N hours."""
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    stmt = (
        select(func.count())
        .select_from(AuditLog)
        .where(
            AuditLog.created_at >= cutoff,
            AuditLog.action.in_(ERROR_ACTIONS),
        )
    )
    return session.execute(stmt).scalar_one()
