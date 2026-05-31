"""Webhook delivery service (EXT-003).

Sends webhook POST requests with HMAC-SHA256 signatures, retries
on failure (3 attempts, exponential backoff), enforces a 30-second
timeout, and auto-disables webhooks after 10 consecutive failures.
Delivery logs are capped at 100 per webhook.
"""

import hashlib
import hmac
import json
import logging
import time
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.backend.models.webhook import Webhook
from src.backend.models.webhook_log import WebhookDeliveryLog

log = logging.getLogger("buzzreach.webhooks")

_MAX_RETRIES = 3
_TIMEOUT_SECONDS = 30
_MAX_CONSECUTIVE_FAILURES = 10
_MAX_DELIVERY_LOGS = 100


def compute_signature(body: bytes, secret: str) -> str:
    """Compute HMAC-SHA256 signature for a webhook payload.

    Args:
        body: Raw request body bytes.
        secret: The webhook's shared secret.

    Returns:
        Signature string in ``sha256=<hex>`` format.
    """
    digest = hmac.new(
        secret.encode(), body, hashlib.sha256
    ).hexdigest()
    return f"sha256={digest}"


def send_webhook(
    session: Session,
    webhook: Webhook,
    event_type: str,
    data: dict[str, Any],
) -> None:
    """Send a webhook POST request with retry logic.

    Builds the payload, signs it, and attempts delivery up to 3 times
    with exponential backoff. Records a delivery log entry and updates
    the webhook's consecutive failure counter.

    Args:
        session: DB session for logging and status updates.
        webhook: The webhook configuration to deliver to.
        event_type: Event name (e.g. ``opportunity_created``).
        data: Event data payload.
    """
    payload = _build_payload(event_type, data, webhook.secret)
    body = json.dumps(payload).encode()

    status_code, response_body, error_msg = _attempt_delivery(
        url=webhook.url, body=body, signature=payload["signature"],
    )
    success = error_msg == ""

    _record_delivery_log(
        session, webhook.id, status_code, response_body,
        success, error_msg,
    )
    _update_failure_counter(session, webhook, success)

    log.info(
        "Webhook delivered" if success else "Webhook delivery failed",
        extra={
            "webhook_id": str(webhook.id),
            "event_type": event_type,
            "success": success,
            "status_code": status_code,
        },
    )


def _build_payload(
    event_type: str,
    data: dict[str, Any],
    secret: str,
) -> dict[str, Any]:
    """Build the signed webhook payload."""
    payload: dict[str, Any] = {
        "event": event_type,
        "timestamp": datetime.now(UTC).isoformat(),
        "data": data,
        "signature": "",
    }
    body_for_sig = json.dumps(
        {k: v for k, v in payload.items() if k != "signature"}
    ).encode()
    payload["signature"] = compute_signature(body_for_sig, secret)
    return payload


def _attempt_delivery(
    url: str, body: bytes, signature: str,
) -> tuple[int | None, str, str]:
    """Try to POST the payload with retries.

    Returns:
        Tuple of (status_code, response_body, error_message).
        error_message is empty on success.
    """
    last_error = ""
    for attempt in range(_MAX_RETRIES):
        try:
            status_code, resp_body = _http_post(url, body, signature)
            if 200 <= status_code < 300:
                return status_code, resp_body, ""
            last_error = f"HTTP {status_code}: {resp_body[:500]}"
        except Exception as exc:
            last_error = str(exc)[:500]

        if attempt < _MAX_RETRIES - 1:
            _backoff_sleep(attempt)

    return None, "", last_error


def _http_post(
    url: str, body: bytes, signature: str,
) -> tuple[int, str]:
    """Execute the HTTP POST request.

    Args:
        url: Destination URL.
        body: JSON body bytes.
        signature: HMAC signature header value.

    Returns:
        Tuple of (status_code, response_body_text).
    """
    req = Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:  # noqa: S310
            return resp.status, resp.read().decode()[:1000]
    except HTTPError as exc:
        return exc.code, exc.read().decode()[:1000]


def _backoff_sleep(attempt: int) -> None:
    """Sleep with exponential backoff between retries."""
    time.sleep(2 ** attempt)


def _record_delivery_log(
    session: Session,
    webhook_id: Any,
    status_code: int | None,
    response_body: str,
    success: bool,
    error_message: str,
) -> None:
    """Write a delivery log entry and trim to 100 per webhook."""
    entry = WebhookDeliveryLog(
        webhook_id=webhook_id,
        status_code=status_code,
        response_body=response_body[:1000],
        success=success,
        error_message=error_message[:1000],
    )
    session.add(entry)
    session.commit()
    _trim_delivery_logs(session, webhook_id)


def _trim_delivery_logs(
    session: Session, webhook_id: Any,
) -> None:
    """Keep only the most recent 100 logs per webhook."""
    count = (
        session.query(func.count(WebhookDeliveryLog.id))
        .filter(WebhookDeliveryLog.webhook_id == webhook_id)
        .scalar()
    )
    if count is None or count <= _MAX_DELIVERY_LOGS:
        return

    excess = count - _MAX_DELIVERY_LOGS
    oldest = (
        session.query(WebhookDeliveryLog.id)
        .filter(WebhookDeliveryLog.webhook_id == webhook_id)
        .order_by(WebhookDeliveryLog.created_at.asc())
        .limit(excess)
        .all()
    )
    ids_to_delete = [row[0] for row in oldest]
    (
        session.query(WebhookDeliveryLog)
        .filter(WebhookDeliveryLog.id.in_(ids_to_delete))
        .delete(synchronize_session="fetch")
    )
    session.commit()


def _update_failure_counter(
    session: Session, webhook: Webhook, success: bool,
) -> None:
    """Update consecutive failure counter; disable after 10."""
    if success:
        webhook.consecutive_failures = 0
    else:
        webhook.consecutive_failures += 1
        if webhook.consecutive_failures >= _MAX_CONSECUTIVE_FAILURES:
            webhook.active = False
            log.info(
                "Webhook auto-disabled",
                extra={
                    "webhook_id": str(webhook.id),
                    "failures": webhook.consecutive_failures,
                },
            )
    session.commit()
