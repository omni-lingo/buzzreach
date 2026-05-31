"""Request/response schemas for the Dashboard API (DASH-001).

DashboardResponse: today's summary (opportunities, tokens, cost, errors).
StatsResponse: per-niche metric aggregation over N days.
ErrorsResponse: list of recent error audit log entries.

These shapes are contracts that a future mobile app will consume.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DashboardResponse(BaseModel):
    """Today's high-level dashboard summary."""

    opportunities_found: int = Field(
        description="Opportunities discovered today",
    )
    acted_on: int = Field(
        description="Opportunities acted on today",
    )
    ai_tokens_used: int = Field(
        description="Total AI tokens (input + output) used today",
    )
    cost_usd: float = Field(
        description="Total AI cost in USD today",
    )
    next_scan_time: datetime | None = Field(
        default=None,
        description="Scheduled time of the next scan (null if unknown)",
    )
    error_count: int = Field(
        description="Number of error events in the last 24 hours",
    )


class MetricAggregateItem(BaseModel):
    """Aggregated values for a single metric name."""

    sum: float
    count: int
    avg: float


class NicheStats(BaseModel):
    """Metrics aggregated for a single niche."""

    niche: str
    period: str = "daily"
    metrics: dict[str, MetricAggregateItem] = Field(default_factory=dict)


class StatsResponse(BaseModel):
    """Per-niche metric aggregation over a requested time period."""

    days: int = Field(description="Number of days covered")
    niches: list[NicheStats] = Field(default_factory=list)


class AuditErrorEntry(BaseModel):
    """A single error entry from the audit log."""

    model_config = {"from_attributes": True}

    id: UUID
    action: str
    resource_type: str
    change_summary: str | None = None
    created_at: datetime


class ErrorsResponse(BaseModel):
    """Recent error entries from the audit log."""

    hours: int = Field(description="Time window in hours")
    errors: list[AuditErrorEntry] = Field(default_factory=list)
