"""Cross-module contract for metrics data (OBSERV-001).

DTO returned by ``MetricsRecorder.get_daily_stats()`` and consumed by
the dashboard API (DASH-001) to render metric summaries.

Consumers: DASH-001 (dashboard routes).
"""

from pydantic import BaseModel, Field


class MetricAggregate(BaseModel):
    """Aggregated values for a single metric name."""

    sum: float = Field(description="Total value across all records")
    count: int = Field(description="Number of records")
    avg: float = Field(description="Average value per record")


class MetricsData(BaseModel):
    """Aggregated metrics for a niche over a time period.

    Used as the API response DTO for the dashboard metrics endpoint.
    """

    niche: str = Field(description="Niche slug the metrics belong to")
    period: str = Field(description="Time period label, e.g. 'daily'")
    metrics: dict[str, dict[str, float]] = Field(
        default_factory=dict,
        description="Mapping of metric_name -> {sum, count, avg}",
    )
