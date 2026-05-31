"""Metrics recorder service (OBSERV-001).

Writes timestamped metric rows to the ``Metric`` table and aggregates
daily stats. All write operations are non-fatal — a failing database
must never crash the calling pipeline.

Consumers:
- PIPE-001 calls ``record_search_run`` after discovery.
- AI-002/003 call ``record_ai_tokens`` after inference.
- DELIV-002 calls ``record_delivery`` after sending.
- DASH-001 calls ``get_daily_stats`` to render the dashboard.
"""

import logging
from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.backend.models.metric import Metric

log = logging.getLogger("buzzreach.observability.metrics")


class MetricsRecorder:
    """Records product metrics and queries daily aggregates."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def record(
        self, metric_name: str, value: float, niche: str,
    ) -> None:
        """Write a single metric row. Non-fatal on DB failure."""
        try:
            row = Metric(
                metric_name=metric_name,
                value=value,
                niche=niche,
            )
            self._session.add(row)
            self._session.commit()
        except Exception:
            self._session.rollback()
            log.error(
                "METRIC_RECORD_FAILED",
                extra={
                    "error_code": "METRIC_RECORD_FAILED",
                    "metric_name": metric_name,
                    "niche": niche,
                },
                exc_info=True,
            )

    def record_search_run(
        self,
        niche: str,
        candidates_found: int,
        queries_run: int,
    ) -> None:
        """Record search discovery metrics for a niche."""
        self.record("candidates_found", float(candidates_found), niche)
        self.record("queries_run", float(queries_run), niche)
        log.info(
            "Search run recorded",
            extra={
                "niche": niche,
                "candidates_found": candidates_found,
                "queries_run": queries_run,
            },
        )

    def record_ai_tokens(
        self,
        niche: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
    ) -> None:
        """Record AI token usage and cost for a niche and model."""
        self.record(f"ai_input_tokens_{model}", float(input_tokens), niche)
        self.record(f"ai_output_tokens_{model}", float(output_tokens), niche)
        self.record("ai_cost_usd", cost_usd, niche)
        log.info(
            "AI tokens recorded",
            extra={
                "niche": niche,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost_usd,
            },
        )

    def record_delivery(
        self,
        niche: str,
        opportunities_sent: int,
        success: bool,
    ) -> None:
        """Record delivery attempt metrics for a niche."""
        self.record("delivery_sent", float(opportunities_sent), niche)
        self.record("delivery_success", 1.0 if success else 0.0, niche)
        log.info(
            "Delivery recorded",
            extra={
                "niche": niche,
                "opportunities_sent": opportunities_sent,
                "success": success,
            },
        )

    def get_daily_stats(
        self, niche: str | None = None,
    ) -> dict[str, dict[str, dict[str, float]]]:
        """Aggregate today's metrics by niche.

        Returns a nested dict:
        ``{niche: {metric_name: {sum, count, avg}}}``
        """
        today_start = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0,
        )
        stmt = select(Metric).where(Metric.timestamp >= today_start)
        if niche is not None:
            stmt = stmt.where(Metric.niche == niche)

        rows = list(self._session.execute(stmt).scalars())
        return _aggregate_rows(rows)


def _aggregate_rows(
    rows: list[Metric],
) -> dict[str, dict[str, dict[str, float]]]:
    """Build {niche: {metric: {sum, count, avg}}} from raw rows."""
    buckets: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list),
    )
    for row in rows:
        buckets[row.niche][row.metric_name].append(row.value)

    result: dict[str, dict[str, dict[str, float]]] = {}
    for niche_key, metrics in buckets.items():
        result[niche_key] = {}
        for metric_name, values in metrics.items():
            total = sum(values)
            count = len(values)
            result[niche_key][metric_name] = {
                "sum": total,
                "count": float(count),
                "avg": total / count if count else 0.0,
            }

    return result
