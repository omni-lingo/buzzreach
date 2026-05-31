"""Tests for MONITOR-001: alert sending and check_all orchestration.

Covers HealthMonitor.send_alert (SMTP, Slack, failure handling)
and check_all (compile + alert logic).
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

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


_PATCH = "src.backend.services.observability.health_monitor"


# ---------------------------------------------------------------------------
# HealthMonitor.send_alert
# ---------------------------------------------------------------------------

class TestSendAlert:
    """send_alert delivers via SMTP or Slack; failures don't crash."""

    @patch(f"{_PATCH}._send_email")
    def test_sends_email_when_smtp_configured(
        self, mock_email: MagicMock, db_session: Session,
    ) -> None:
        from src.backend.services.observability.health_monitor import (
            HealthMonitor,
        )

        settings = _make_settings(smtp_host="mail.example.com")
        monitor = HealthMonitor(session=db_session, settings=settings)
        monitor.send_alert("Test alert", "Something broke")
        mock_email.assert_called_once()

    @patch(f"{_PATCH}._send_slack")
    def test_sends_slack_when_webhook_configured(
        self, mock_slack: MagicMock, db_session: Session,
    ) -> None:
        from src.backend.services.observability.health_monitor import (
            HealthMonitor,
        )

        settings = _make_settings(
            slack_webhook_url="https://hooks.slack.com/test",
        )
        monitor = HealthMonitor(session=db_session, settings=settings)
        monitor.send_alert("Test alert", "Something broke")
        mock_slack.assert_called_once()

    @patch(f"{_PATCH}._send_email")
    def test_alert_failure_does_not_raise(
        self, mock_email: MagicMock, db_session: Session,
    ) -> None:
        from src.backend.services.observability.health_monitor import (
            HealthMonitor,
        )

        mock_email.side_effect = OSError("connection refused")
        settings = _make_settings(smtp_host="mail.example.com")
        monitor = HealthMonitor(session=db_session, settings=settings)
        monitor.send_alert("Test alert", "Something broke")

    @patch(f"{_PATCH}.log")
    @patch(f"{_PATCH}._send_email")
    def test_alert_failure_is_logged(
        self,
        mock_email: MagicMock,
        mock_log: MagicMock,
        db_session: Session,
    ) -> None:
        from src.backend.services.observability.health_monitor import (
            HealthMonitor,
        )

        mock_email.side_effect = OSError("connection refused")
        settings = _make_settings(smtp_host="mail.example.com")
        monitor = HealthMonitor(session=db_session, settings=settings)
        monitor.send_alert("Test alert", "Something broke")
        mock_log.error.assert_called_once()


# ---------------------------------------------------------------------------
# HealthMonitor.check_all
# ---------------------------------------------------------------------------

class TestCheckAll:
    """check_all compiles results and sends a single alert."""

    @patch(f"{_PATCH}.load_all_configs")
    def test_check_all_sends_alert_on_issues(
        self, mock_configs: MagicMock, db_session: Session,
    ) -> None:
        from contracts.config.product_config import ProductConfig
        from src.backend.services.observability.health_monitor import (
            HealthMonitor,
        )

        mock_configs.return_value = [
            ProductConfig(
                slug="irs", product_url="https://example.com",
                pitch="test", niche="tax", keywords=["irs"],
                tone="helpful", mention="check it out",
            ),
        ]
        _insert_audit(
            db_session, action="search_failed", resource_type="search",
            change_summary="SEARCH_PROVIDER_ERROR: timeout", hours_ago=1,
        )
        settings = _make_settings(smtp_host="mail.example.com")
        monitor = HealthMonitor(session=db_session, settings=settings)

        with patch.object(monitor, "send_alert") as mock_alert:
            monitor.check_all()
            mock_alert.assert_called_once()

    @patch(f"{_PATCH}.load_all_configs")
    def test_check_all_no_alert_when_healthy(
        self, mock_configs: MagicMock, db_session: Session,
    ) -> None:
        from contracts.config.product_config import ProductConfig
        from src.backend.services.observability.health_monitor import (
            HealthMonitor,
        )

        mock_configs.return_value = [
            ProductConfig(
                slug="irs", product_url="https://example.com",
                pitch="test", niche="tax", keywords=["irs"],
                tone="helpful", mention="check it out",
            ),
        ]
        _insert_audit(
            db_session, action="scan_completed", resource_type="scan",
            change_summary="tax: 3 drafted", hours_ago=1,
        )
        settings = _make_settings(smtp_host="mail.example.com")
        monitor = HealthMonitor(session=db_session, settings=settings)

        with patch.object(monitor, "send_alert") as mock_alert:
            monitor.check_all()
            mock_alert.assert_not_called()
