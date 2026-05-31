"""Digest sender for the delivery module (DELIV-002).

Sends a pre-built Digest via email (SMTP) and/or Slack webhook depending
on which transport settings are configured. On success, marks included
opportunities as ``delivered``, logs to the audit table, and records a
delivery metric. On failure, raises ``AppError(code="DELIVERY_FAILED")``,
records a failure metric, and leaves opportunity status unchanged.
"""

import logging
import smtplib
from datetime import UTC, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Protocol
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session

from contracts.delivery.digest import Digest
from src.backend.errors import AppError
from src.backend.models.opportunity import Opportunity, OpportunityStatus

log = logging.getLogger("buzzreach")


class _Settings(Protocol):
    """Subset of Settings fields used by the sender."""

    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    slack_webhook_url: str


class _AuditService(Protocol):
    """Subset of AuditService used by the sender."""

    def log(
        self,
        action: str,
        resource_type: str,
        *,
        change_summary: str | None = None,
    ) -> None: ...


class _MetricsRecorder(Protocol):
    """Subset of MetricsRecorder used by the sender."""

    def record_delivery(
        self,
        niche: str,
        opportunities_sent: int,
        *,
        success: bool,
    ) -> None: ...


def send_digest(
    digest: Digest,
    settings: _Settings,
    audit_service: _AuditService,
    metrics_recorder: _MetricsRecorder,
    session: Session,
) -> None:
    """Send a digest via configured transports.

    Args:
        digest: The pre-built digest to send.
        settings: App settings with SMTP / Slack config.
        audit_service: Audit logger for recording the send action.
        metrics_recorder: Metrics recorder for delivery tracking.
        session: SQLAlchemy session for updating opportunity status.
    """
    if not digest.opportunity_ids:
        return

    niche = _resolve_niche(digest, session)
    count = len(digest.opportunity_ids)
    channel = _pick_channel(settings)

    try:
        _dispatch(digest, settings, channel)
    except Exception as exc:
        metrics_recorder.record_delivery(niche, count, success=False)
        log.error(
            "Digest delivery failed",
            extra={
                "error_code": "DELIVERY_FAILED",
                "channel": channel,
                "count": count,
                "niche": niche,
            },
            exc_info=True,
        )
        raise AppError(
            code="DELIVERY_FAILED",
            message=f"Failed to send digest via {channel}: {exc}",
        ) from exc

    _mark_delivered(digest, session)
    audit_service.log(
        "digest_sent",
        "digest",
        change_summary=f"Sent {count} opportunities via {channel}",
    )
    metrics_recorder.record_delivery(niche, count, success=True)

    log.info(
        "Digest sent",
        extra={"channel": channel, "count": count, "niche": niche},
    )


def _resolve_niche(digest: Digest, session: Session) -> str:
    """Look up the niche from the first opportunity in the digest."""
    if not digest.opportunity_ids:
        return "unknown"
    opp = session.get(Opportunity, digest.opportunity_ids[0])
    if opp is None:
        return "unknown"
    return opp.niche


def _pick_channel(settings: _Settings) -> str:
    """Determine which transport channels are configured."""
    has_smtp = bool(settings.smtp_host)
    has_slack = bool(settings.slack_webhook_url)
    if has_smtp and has_slack:
        return "email+slack"
    if has_smtp:
        return "email"
    if has_slack:
        return "slack"
    return "none"


def _dispatch(
    digest: Digest,
    settings: _Settings,
    channel: str,
) -> None:
    """Route the digest to the correct transport(s)."""
    if "email" in channel:
        _send_email(digest, settings)
    if "slack" in channel:
        _send_slack(digest, settings)


def _mark_delivered(digest: Digest, session: Session) -> None:
    """Transition opportunities to ``delivered`` and set ``delivered_at``."""
    now = datetime.now(UTC)
    for opp_id in digest.opportunity_ids:
        opp = session.get(Opportunity, opp_id)
        if opp is not None:
            opp.status = OpportunityStatus.DELIVERED
            opp.delivered_at = now
    session.commit()


def _send_email(digest: Digest, settings: _Settings) -> None:
    """Send the digest via SMTP."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = digest.subject
    msg["From"] = settings.smtp_from_email
    msg["To"] = settings.smtp_from_email
    msg.attach(MIMEText(digest.text_body, "plain"))
    msg.attach(MIMEText(digest.html_body, "html"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)


def _send_slack(digest: Digest, settings: _Settings) -> None:
    """Post the digest text to a Slack incoming webhook."""
    import json

    payload = json.dumps({"text": digest.text_body}).encode()
    req = Request(
        settings.slack_webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req) as resp:  # noqa: S310
        resp.read()
