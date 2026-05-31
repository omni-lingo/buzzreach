"""Tests for MONITOR-001: health check detection logic.

Covers HealthResult contract and HealthMonitor check methods
(check_last_scan, check_search_failures, check_ai_failures,
check_delivery_failures).
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from contracts.observability.health_result import HealthResult
from src.backend.models.audit_log import AuditLog

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _insert_audit(
    session: Session,
    action: str,
    resource_type: str = "scan",
    *,
    change_summary: str | None = None,
    hours_ago: float = 0,
) -> AuditLog:
    """Insert an AuditLog row at a given time offset."""
    row = AuditLog(
        id=uuid.uuid4(),
        action=action,
        resource_type=resource_type,
        change_summary=change_summary,
        created_at=datetime.now(UTC) - timedelta(hours=hours_ago),
    )
    session.add(row)
    session.commit()
    return row


def _make_settings(**overrides: object) -> MagicMock:
    """Build a mock Settings with alert-related defaults."""
    defaults = {
        "smtp_host": "",
        "smtp_port": 587,
        "smtp_username": "",
        "smtp_password": "",
        "smtp_from_email": "noreply@buzzreach.app",
        "slack_webhook_url": "",
        "config_dir": "config",
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, val in defaults.items():
        setattr(mock, key, val)
    return mock


# ---------------------------------------------------------------------------
# HealthResult contract
# ---------------------------------------------------------------------------

class TestHealthResult:
    """HealthResult DTO behaviour."""

    def test_healthy_when_no_issues(self) -> None:
        result = HealthResult(
            niche="tax", scan_ok=True, scan_detail="Last scan 1h ago",
        )
        assert result.is_healthy is True

    def test_unhealthy_when_scan_not_ok(self) -> None:
        result = HealthResult(
            niche="tax", scan_ok=False, scan_detail="No scan in 4h",
        )
        assert result.is_healthy is False

    def test_unhealthy_when_search_errors(self) -> None:
        result = HealthResult(
            niche="tax", scan_ok=True, scan_detail="OK",
            search_errors=["provider timeout"],
        )
        assert result.is_healthy is False

    def test_unhealthy_when_ai_errors(self) -> None:
        result = HealthResult(
            niche="tax", scan_ok=True, scan_detail="OK",
            ai_errors=["rate limit"],
        )
        assert result.is_healthy is False

    def test_unhealthy_when_delivery_errors(self) -> None:
        result = HealthResult(
            niche="tax", scan_ok=True, scan_detail="OK",
            delivery_errors=["SMTP refused"],
        )
        assert result.is_healthy is False


# ---------------------------------------------------------------------------
# HealthMonitor.check_last_scan
# ---------------------------------------------------------------------------

class TestCheckLastScan:
    """check_last_scan detects overdue or failed scans."""

    def test_scan_ok_when_recent_success(self, db_session: Session) -> None:
        from src.backend.services.observability.health_monitor import (
            HealthMonitor,
        )

        _insert_audit(
            db_session, action="scan_completed", resource_type="scan",
            change_summary="tax: 3 drafted", hours_ago=1,
        )
        monitor = HealthMonitor(session=db_session, settings=_make_settings())
        result = monitor.check_last_scan("tax")
        assert result.scan_ok is True

    def test_scan_overdue_when_no_recent(self, db_session: Session) -> None:
        from src.backend.services.observability.health_monitor import (
            HealthMonitor,
        )

        _insert_audit(
            db_session, action="scan_completed", resource_type="scan",
            change_summary="tax: 3 drafted", hours_ago=5,
        )
        monitor = HealthMonitor(session=db_session, settings=_make_settings())
        result = monitor.check_last_scan("tax")
        assert result.scan_ok is False
        assert "overdue" in result.scan_detail.lower()

    def test_scan_overdue_when_no_scan_ever(
        self, db_session: Session,
    ) -> None:
        from src.backend.services.observability.health_monitor import (
            HealthMonitor,
        )

        monitor = HealthMonitor(session=db_session, settings=_make_settings())
        result = monitor.check_last_scan("tax")
        assert result.scan_ok is False


# ---------------------------------------------------------------------------
# HealthMonitor.check_search_failures
# ---------------------------------------------------------------------------

class TestCheckSearchFailures:
    """check_search_failures finds SEARCH_PROVIDER_ERROR entries."""

    def test_returns_errors_from_audit(self, db_session: Session) -> None:
        from src.backend.services.observability.health_monitor import (
            HealthMonitor,
        )

        _insert_audit(
            db_session, action="search_failed", resource_type="search",
            change_summary="SEARCH_PROVIDER_ERROR: timeout", hours_ago=2,
        )
        monitor = HealthMonitor(session=db_session, settings=_make_settings())
        errors = monitor.check_search_failures(hours=24)
        assert len(errors) == 1
        assert "SEARCH_PROVIDER_ERROR" in errors[0]

    def test_ignores_old_errors(self, db_session: Session) -> None:
        from src.backend.services.observability.health_monitor import (
            HealthMonitor,
        )

        _insert_audit(
            db_session, action="search_failed", resource_type="search",
            change_summary="SEARCH_PROVIDER_ERROR: timeout", hours_ago=30,
        )
        monitor = HealthMonitor(session=db_session, settings=_make_settings())
        errors = monitor.check_search_failures(hours=24)
        assert len(errors) == 0

    def test_returns_empty_when_no_failures(
        self, db_session: Session,
    ) -> None:
        from src.backend.services.observability.health_monitor import (
            HealthMonitor,
        )

        monitor = HealthMonitor(session=db_session, settings=_make_settings())
        errors = monitor.check_search_failures(hours=24)
        assert errors == []


# ---------------------------------------------------------------------------
# HealthMonitor.check_ai_failures / check_delivery_failures
# ---------------------------------------------------------------------------

class TestCheckAiFailures:
    """check_ai_failures finds AI_PROVIDER_ERROR entries."""

    def test_returns_ai_errors(self, db_session: Session) -> None:
        from src.backend.services.observability.health_monitor import (
            HealthMonitor,
        )

        _insert_audit(
            db_session, action="ai_failed", resource_type="ai",
            change_summary="AI_PROVIDER_ERROR: rate limit", hours_ago=1,
        )
        monitor = HealthMonitor(session=db_session, settings=_make_settings())
        errors = monitor.check_ai_failures(hours=24)
        assert len(errors) == 1
        assert "AI_PROVIDER_ERROR" in errors[0]


class TestCheckDeliveryFailures:
    """check_delivery_failures finds DELIVERY_FAILED entries."""

    def test_returns_delivery_errors(self, db_session: Session) -> None:
        from src.backend.services.observability.health_monitor import (
            HealthMonitor,
        )

        _insert_audit(
            db_session, action="delivery_failed", resource_type="delivery",
            change_summary="DELIVERY_FAILED: SMTP refused", hours_ago=1,
        )
        monitor = HealthMonitor(session=db_session, settings=_make_settings())
        errors = monitor.check_delivery_failures(hours=24)
        assert len(errors) == 1
        assert "DELIVERY_FAILED" in errors[0]
