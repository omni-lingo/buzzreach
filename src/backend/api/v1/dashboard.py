"""Dashboard API endpoints (DASH-001).

GET /api/v1/dashboard — today's summary (opportunities, tokens, cost, errors).
GET /api/v1/dashboard/stats — per-niche metric aggregation over N days.
GET /api/v1/dashboard/errors — recent error audit log entries.

No auth required for MVP. All endpoints use Pydantic response_model.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.backend.api.v1.dashboard_schemas import (
    DashboardResponse,
    ErrorsResponse,
    StatsResponse,
)
from src.backend.db.session import get_session
from src.backend.services.dashboard_queries import (
    get_niche_stats,
    get_recent_errors,
)
from src.backend.services.dashboard_service import (
    count_recent_errors,
    count_today_acted,
    count_today_opportunities,
    sum_today_ai_tokens,
    sum_today_cost,
)

log = logging.getLogger("buzzreach.api.v1.dashboard")

router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["dashboard"],
)

SessionDep = Annotated[Session, Depends(get_session)]


@router.get(
    "",
    response_model=DashboardResponse,
)
def get_dashboard(session: SessionDep) -> DashboardResponse:
    """Return today's high-level dashboard summary."""
    result = DashboardResponse(
        opportunities_found=count_today_opportunities(session),
        acted_on=count_today_acted(session),
        ai_tokens_used=sum_today_ai_tokens(session),
        cost_usd=sum_today_cost(session),
        next_scan_time=None,
        error_count=count_recent_errors(session),
    )
    log.info(
        "Dashboard summary served",
        extra={
            "opportunities_found": result.opportunities_found,
            "error_count": result.error_count,
        },
    )
    return result


@router.get(
    "/stats",
    response_model=StatsResponse,
)
def get_dashboard_stats(
    session: SessionDep,
    niche: str | None = Query(default=None, description="Filter by niche"),
    days: int = Query(default=7, ge=1, le=90, description="Days to cover"),
) -> StatsResponse:
    """Return per-niche metric aggregation over the last N days."""
    niches = get_niche_stats(session, days=days, niche=niche)
    log.info(
        "Dashboard stats served",
        extra={"niche_count": len(niches), "days": days},
    )
    return StatsResponse(days=days, niches=niches)


@router.get(
    "/errors",
    response_model=ErrorsResponse,
)
def get_dashboard_errors(
    session: SessionDep,
    hours: int = Query(
        default=24, ge=1, le=168, description="Hours to look back",
    ),
) -> ErrorsResponse:
    """Return recent error audit log entries."""
    errors = get_recent_errors(session, hours=hours)
    log.info(
        "Dashboard errors served",
        extra={"error_count": len(errors), "hours": hours},
    )
    return ErrorsResponse(hours=hours, errors=errors)
