"""Health check job — cron entrypoint stub (JOB-001).

CLI-invokable as ``python -m src.backend.jobs.health_check``.
MONITOR-001 will implement the full ``run_health_check()`` logic.
This module provides the CLI wrapper and a placeholder until then.
"""

import logging
import sys

log = logging.getLogger("buzzreach.jobs.health_check")


def run_health_check() -> None:
    """Run a health check across all monitored niches.

    Delegates to MONITOR-001's HealthMonitor once it exists.
    Until then, logs a placeholder message.
    """
    try:
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
    except ImportError:
        log.warning(
            "Health monitor not available yet",
            extra={"reason": "MONITOR-001 not implemented"},
        )


if __name__ == "__main__":
    from src.backend.logging_config import setup_logging

    setup_logging()

    try:
        run_health_check()
    except Exception:
        log.error("Health check failed", exc_info=True)
        sys.exit(1)
