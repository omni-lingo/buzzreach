"""Dashboard query helpers for stats and errors (DASH-001, L2).

Provides per-niche metric aggregation and error log retrieval,
consumed by the dashboard API routes.
"""

import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.backend.api.v1.dashboard_schemas import (
    AuditErrorEntry,
    MetricAggregateItem,
    NicheStats,
)
from src.backend.models.audit_log import AuditLog
from src.backend.models.metric import Metric
from src.backend.services.dashboard_service import ERROR_ACTIONS

log = logging.getLogger("buzzreach.services.dashboard_queries")


def get_niche_stats(
    session: Session,
    days: int = 7,
    niche: str | None = None,
) -> list[NicheStats]:
    """Aggregate metrics by niche over the last N days."""
    cutoff = datetime.now(UTC) - timedelta(days=days)
    stmt = select(Metric).where(Metric.timestamp >= cutoff)
    if niche is not None:
        stmt = stmt.where(Metric.niche == niche)

    rows = list(session.execute(stmt).scalars())
    return _build_niche_stats(rows)


def _build_niche_stats(rows: list[Metric]) -> list[NicheStats]:
    """Build NicheStats list from raw metric rows."""
    buckets: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list),
    )
    for row in rows:
        buckets[row.niche][row.metric_name].append(row.value)

    result: list[NicheStats] = []
    for niche_key, metrics in sorted(buckets.items()):
        agg: dict[str, MetricAggregateItem] = {}
        for metric_name, values in sorted(metrics.items()):
            total = sum(values)
            count = len(values)
            agg[metric_name] = MetricAggregateItem(
                sum=total,
                count=count,
                avg=total / count if count else 0.0,
            )
        result.append(NicheStats(niche=niche_key, metrics=agg))
    return result


def get_recent_errors(
    session: Session,
    hours: int = 24,
) -> list[AuditErrorEntry]:
    """Fetch error audit log entries from the last N hours."""
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    stmt = (
        select(AuditLog)
        .where(
            AuditLog.created_at >= cutoff,
            AuditLog.action.in_(ERROR_ACTIONS),
        )
        .order_by(AuditLog.created_at.desc())
    )
    rows = list(session.execute(stmt).scalars())
    return [AuditErrorEntry.model_validate(r) for r in rows]
