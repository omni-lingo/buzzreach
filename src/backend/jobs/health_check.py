"""Health check job — cron entrypoint (MONITOR-001).

CLI-invokable as ``python -m src.backend.jobs.health_check``.
Delegates to the HealthMonitor service for all checks and alerting.
"""

import logging
import sys

log = logging.getLogger("buzzreach.jobs.health_check")


def run_health_check() -> None:
    """Run a health check across all monitored niches."""
    from src.backend.db.session import get_session_factory  # noqa: PLC0415
    from src.backend.services.observability.health_monitor import (  # noqa: PLC0415
        HealthMonitor,
    )
    from src.backend.settings import Settings  # noqa: PLC0415

    settings = Settings()
    session = get_session_factory()()
    try:
        monitor = HealthMonitor(session=session, settings=settings)
        monitor.check_all()
    finally:
        session.close()


if __name__ == "__main__":
    from src.backend.logging_config import setup_logging

    setup_logging()

    try:
        run_health_check()
    except Exception:
        log.error("Health check failed", exc_info=True)
        sys.exit(1)
