"""Health monitor service (MONITOR-001).

Queries the AuditLog table to detect scan failures, search/AI/delivery
errors, and sends a consolidated alert via SMTP or Slack. Alert send
failures are logged but never raised.

CLI-callable via ``src.backend.jobs.health_check_job``.
"""

import json
import logging
import smtplib
from datetime import UTC, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Protocol
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.orm import Session

from contracts.observability.health_result import HealthResult
from src.backend.models.audit_log import AuditLog
from src.backend.services.config_loader import load_all_configs

log = logging.getLogger("buzzreach.observability.health_monitor")

_SCAN_OVERDUE_HOURS: int = 3


class _Settings(Protocol):
    """Subset of Settings fields used by the health monitor."""

    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    slack_webhook_url: str
    config_dir: object


class HealthMonitor:
    """Checks system health via audit log and sends alerts."""

    def __init__(self, session: Session, settings: _Settings) -> None:
        self._session = session
        self._settings = settings

    def check_last_scan(self, niche: str) -> HealthResult:
        """Check if a scan ran successfully within the last 3 hours."""
        cutoff = datetime.now(UTC) - timedelta(hours=_SCAN_OVERDUE_HOURS)
        stmt = (
            select(AuditLog)
            .where(
                AuditLog.action == "scan_completed",
                AuditLog.created_at >= cutoff,
            )
            .order_by(AuditLog.created_at.desc())
        )
        rows = list(self._session.execute(stmt).scalars())
        matching = _filter_by_niche(rows, niche)

        if matching:
            detail = f"Last scan {_ago(matching[0].created_at)} ago"
            return HealthResult(
                niche=niche, scan_ok=True, scan_detail=detail,
            )

        return HealthResult(
            niche=niche,
            scan_ok=False,
            scan_detail=f"Scan overdue — no success in last {_SCAN_OVERDUE_HOURS}h",
        )

    def check_search_failures(self, hours: int = 24) -> list[str]:
        """Find SEARCH_PROVIDER_ERROR audit entries in the window."""
        return self._find_errors("SEARCH_PROVIDER_ERROR", hours)

    def check_ai_failures(self, hours: int = 24) -> list[str]:
        """Find AI_PROVIDER_ERROR audit entries in the window."""
        return self._find_errors("AI_PROVIDER_ERROR", hours)

    def check_delivery_failures(self, hours: int = 24) -> list[str]:
        """Find DELIVERY_FAILED audit entries in the window."""
        return self._find_errors("DELIVERY_FAILED", hours)

    def send_alert(self, subject: str, body: str) -> None:
        """Send an alert via SMTP or Slack. Failures are logged only."""
        try:
            if self._settings.smtp_host:
                _send_email(subject, body, self._settings)
            if self._settings.slack_webhook_url:
                _send_slack(subject, body, self._settings)
        except Exception:
            log.error(
                "Alert send failed",
                extra={
                    "error_code": "ALERT_SEND_FAILED",
                    "subject": subject,
                },
                exc_info=True,
            )

    def check_all(self) -> list[HealthResult]:
        """Run all checks across configured niches and alert if needed."""
        from pathlib import Path  # noqa: PLC0415

        configs = load_all_configs(Path(str(self._settings.config_dir)))
        results: list[HealthResult] = []
        search_errors = self.check_search_failures()
        ai_errors = self.check_ai_failures()
        delivery_errors = self.check_delivery_failures()

        for cfg in configs:
            scan_result = self.check_last_scan(cfg.niche)
            result = HealthResult(
                niche=cfg.niche,
                scan_ok=scan_result.scan_ok,
                scan_detail=scan_result.scan_detail,
                search_errors=search_errors,
                ai_errors=ai_errors,
                delivery_errors=delivery_errors,
            )
            results.append(result)

        unhealthy = [r for r in results if not r.is_healthy]
        if unhealthy:
            subject, body = _build_alert_message(unhealthy)
            self.send_alert(subject, body)

        _log_check_summary(results)
        return results

    def _find_errors(self, error_code: str, hours: int) -> list[str]:
        """Query audit log for entries containing the given error code."""
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        stmt = (
            select(AuditLog)
            .where(AuditLog.created_at >= cutoff)
            .order_by(AuditLog.created_at.desc())
        )
        rows = list(self._session.execute(stmt).scalars())
        return [
            row.change_summary
            for row in rows
            if row.change_summary and error_code in row.change_summary
        ]


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _filter_by_niche(rows: list[AuditLog], niche: str) -> list[AuditLog]:
    """Keep only rows whose change_summary mentions the niche."""
    return [
        r for r in rows
        if r.change_summary and niche in r.change_summary
    ]


def _ago(dt: datetime) -> str:
    """Human-readable time-since string."""
    now = datetime.now(UTC)
    aware_dt = dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    delta = now - aware_dt
    minutes = int(delta.total_seconds() / 60)
    if minutes < 60:
        return f"{minutes}m"
    return f"{minutes // 60}h {minutes % 60}m"


def _build_alert_message(
    unhealthy: list[HealthResult],
) -> tuple[str, str]:
    """Compile a single alert subject + body from unhealthy results."""
    subject = f"BuzzReach health alert — {len(unhealthy)} issue(s)"
    lines: list[str] = []
    for result in unhealthy:
        lines.append(f"[{result.niche}] scan: {result.scan_detail}")
        for err in result.search_errors:
            lines.append(f"  search: {err}")
        for err in result.ai_errors:
            lines.append(f"  ai: {err}")
        for err in result.delivery_errors:
            lines.append(f"  delivery: {err}")
    return subject, "\n".join(lines)


def _send_email(
    subject: str, body: str, settings: _Settings,
) -> None:
    """Send an alert email via SMTP."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from_email
    msg["To"] = settings.smtp_from_email
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)


def _send_slack(
    subject: str, body: str, settings: _Settings,
) -> None:
    """Post the alert text to a Slack incoming webhook."""
    payload = json.dumps({"text": f"*{subject}*\n{body}"}).encode()
    req = Request(
        settings.slack_webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req) as resp:  # noqa: S310
        resp.read()


def _log_check_summary(results: list[HealthResult]) -> None:
    """Emit structured log summarising check outcomes."""
    healthy = sum(1 for r in results if r.is_healthy)
    unhealthy = len(results) - healthy
    log.info(
        "Health check complete",
        extra={
            "total_niches": len(results),
            "healthy": healthy,
            "unhealthy": unhealthy,
        },
    )
