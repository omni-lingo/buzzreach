"""Health check job — cron entrypoint (MONITOR-001).

Checks all configured niches for overdue scans, search/AI/delivery
errors, compiles a single alert, and sends if issues are found.
CLI-invokable as ``python -m src.backend.jobs.health_check_job``.
Add to crontab to run every 1 hour.
"""

import logging
import sys

from sqlalchemy.orm import Session

from contracts.observability.health_result import HealthResult

log = logging.getLogger("buzzreach.jobs.health_check_job")


def run_health_check(
    session: Session,
    settings: object,
) -> list[HealthResult]:
    """Run health checks across all niches and alert on issues.

    Args:
        session: SQLAlchemy session for DB queries.
        settings: Application settings with alert config.

    Returns:
        List of HealthResult for each configured niche.
    """
    from src.backend.services.observability.health_monitor import (  # noqa: PLC0415
        HealthMonitor,
    )

    monitor = HealthMonitor(session=session, settings=settings)
    return monitor.check_all()


def _cli_main() -> None:
    """CLI entrypoint for ``python -m src.backend.jobs.health_check_job``."""
    from src.backend.db.session import get_session_factory  # noqa: PLC0415
    from src.backend.logging_config import setup_logging  # noqa: PLC0415
    from src.backend.settings import Settings  # noqa: PLC0415

    setup_logging()
    _settings = Settings()
    _session = get_session_factory()()

    try:
        results = run_health_check(
            session=_session, settings=_settings,
        )
        healthy = sum(1 for r in results if r.is_healthy)
        log.info(
            "Health check finished",
            extra={
                "total": len(results),
                "healthy": healthy,
                "unhealthy": len(results) - healthy,
            },
        )
    except Exception:
        log.error("Health check failed", exc_info=True)
        sys.exit(1)
    finally:
        _session.close()


if __name__ == "__main__":
    _cli_main()
