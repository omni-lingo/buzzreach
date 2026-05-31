"""Webhook management API endpoints (EXT-003).

GET    /api/v1/webhooks              — list user's webhooks
POST   /api/v1/webhooks              — create webhook
POST   /api/v1/webhooks/{id}/test    — send test event
PUT    /api/v1/webhooks/{id}         — update webhook
DELETE /api/v1/webhooks/{id}         — delete webhook
GET    /api/v1/webhooks/{id}/logs    — delivery history

All endpoints require JWT authentication and are rate-limited.
Max 10 webhooks per user.
"""

import logging
import uuid as _uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from contracts.auth.user import UserData
from src.backend.api.auth_deps import get_current_user
from src.backend.api.rate_limit_middleware import require_rate_limit
from src.backend.api.webhook_schemas import (
    DeliveryLogResponse,
    WebhookCreate,
    WebhookResponse,
    WebhookUpdate,
)
from src.backend.db.session import get_session
from src.backend.models.webhook import Webhook
from src.backend.models.webhook_log import WebhookDeliveryLog
from src.backend.services.webhook_service import send_webhook

log = logging.getLogger("buzzreach.api.webhooks")

_MAX_WEBHOOKS_PER_USER = 10

router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["webhooks"],
    dependencies=[Depends(require_rate_limit)],
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[UserData, Depends(get_current_user)]


@router.get("", response_model=list[WebhookResponse])
def list_webhooks(
    session: SessionDep, user: CurrentUser,
) -> list[WebhookResponse]:
    """List all webhooks for the authenticated user."""
    rows = (
        session.query(Webhook)
        .filter(Webhook.user_id == user.id)
        .order_by(Webhook.created_at.desc())
        .all()
    )
    log.info(
        "Webhooks listed",
        extra={"user_id": str(user.id), "count": len(rows)},
    )
    return [WebhookResponse.model_validate(r) for r in rows]


@router.post("", response_model=WebhookResponse, status_code=201)
def create_webhook(
    body: WebhookCreate,
    session: SessionDep,
    user: CurrentUser,
) -> WebhookResponse:
    """Create a new webhook (max 10 per user)."""
    _enforce_webhook_limit(session, user.id)
    _validate_url(body.url)

    wh = Webhook(
        user_id=user.id,
        url=body.url,
        event_type=body.event_type,
    )
    session.add(wh)
    session.commit()

    log.info(
        "Webhook created",
        extra={"webhook_id": str(wh.id), "user_id": str(user.id)},
    )
    return WebhookResponse.model_validate(wh)


@router.post("/{webhook_id}/test", status_code=200)
def test_webhook(
    webhook_id: _uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
) -> dict[str, str]:
    """Send a test event to verify webhook endpoint."""
    wh = _get_user_webhook(session, webhook_id, user.id)
    test_data = {
        "id": "test-opp-000",
        "url": "https://example.com/test",
        "title": "Test opportunity",
        "draft": "This is a test webhook delivery.",
    }
    send_webhook(
        session=session,
        webhook=wh,
        event_type=wh.event_type,
        data=test_data,
    )
    log.info(
        "Webhook test sent",
        extra={"webhook_id": str(wh.id), "user_id": str(user.id)},
    )
    return {"status": "test_sent"}


@router.put("/{webhook_id}", response_model=WebhookResponse)
def update_webhook(
    webhook_id: _uuid.UUID,
    body: WebhookUpdate,
    session: SessionDep,
    user: CurrentUser,
) -> WebhookResponse:
    """Update an existing webhook."""
    wh = _get_user_webhook(session, webhook_id, user.id)

    if body.url is not None:
        _validate_url(body.url)
        wh.url = body.url
    if body.event_type is not None:
        wh.event_type = body.event_type
    if body.active is not None:
        wh.active = body.active
        if body.active:
            wh.consecutive_failures = 0

    session.commit()
    log.info(
        "Webhook updated",
        extra={"webhook_id": str(wh.id), "user_id": str(user.id)},
    )
    return WebhookResponse.model_validate(wh)


@router.delete("/{webhook_id}", status_code=204)
def delete_webhook(
    webhook_id: _uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
) -> None:
    """Delete a webhook and its delivery logs."""
    wh = _get_user_webhook(session, webhook_id, user.id)
    (
        session.query(WebhookDeliveryLog)
        .filter(WebhookDeliveryLog.webhook_id == wh.id)
        .delete()
    )
    session.delete(wh)
    session.commit()
    log.info(
        "Webhook deleted",
        extra={"webhook_id": str(wh.id), "user_id": str(user.id)},
    )


@router.get(
    "/{webhook_id}/logs",
    response_model=list[DeliveryLogResponse],
)
def list_delivery_logs(
    webhook_id: _uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
) -> list[DeliveryLogResponse]:
    """List delivery history for a webhook (most recent first)."""
    wh = _get_user_webhook(session, webhook_id, user.id)
    rows = (
        session.query(WebhookDeliveryLog)
        .filter(WebhookDeliveryLog.webhook_id == wh.id)
        .order_by(WebhookDeliveryLog.created_at.desc())
        .limit(100)
        .all()
    )
    return [DeliveryLogResponse.model_validate(r) for r in rows]


def _get_user_webhook(
    session: Session,
    webhook_id: _uuid.UUID,
    user_id: _uuid.UUID,
) -> Webhook:
    """Fetch a webhook owned by the user, or raise 404."""
    wh = session.get(Webhook, webhook_id)
    if wh is None or wh.user_id != user_id:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "WEBHOOK_NOT_FOUND",
                "message": "Webhook not found",
            },
        )
    return wh


def _enforce_webhook_limit(
    session: Session, user_id: _uuid.UUID,
) -> None:
    """Raise 400 if user has reached the max webhook count."""
    count = (
        session.query(func.count(Webhook.id))
        .filter(Webhook.user_id == user_id)
        .scalar()
    )
    if count is not None and count >= _MAX_WEBHOOKS_PER_USER:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "WEBHOOK_LIMIT_REACHED",
                "message": f"Maximum {_MAX_WEBHOOKS_PER_USER} webhooks per user",
            },
        )


def _validate_url(url: str) -> None:
    """Ensure URL uses HTTPS."""
    if not url.startswith("https://"):
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_WEBHOOK_URL",
                "message": "Webhook URL must use HTTPS",
            },
        )
