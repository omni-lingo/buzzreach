"""Cross-module contract for health check results (MONITOR-001).

Used by the health monitor service and health check job to communicate
check outcomes. Consumers: health_check_job.py.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class HealthResult:
    """Outcome of a single niche health check."""

    niche: str
    scan_ok: bool
    scan_detail: str
    search_errors: list[str] = field(default_factory=list)
    ai_errors: list[str] = field(default_factory=list)
    delivery_errors: list[str] = field(default_factory=list)

    @property
    def is_healthy(self) -> bool:
        """Return True when no issues were detected."""
        return (
            self.scan_ok
            and not self.search_errors
            and not self.ai_errors
            and not self.delivery_errors
        )
