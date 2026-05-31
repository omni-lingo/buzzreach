"""Cross-module contract for webhook integration data (EXT-003).

Consumers: webhook_service (sends payloads), webhooks API (CRUD),
delivery/sender (triggers on events). Changing this file breaks those
modules at import time.
"""

import enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class WebhookEventType(enum.StrEnum):
    """Supported webhook event types."""

    OPPORTUNITY_CREATED = "opportunity_created"
    DAILY_DIGEST = "daily_digest"


class WebhookData(BaseModel):
    """Public webhook representation for cross-module use."""

    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    url: str
    event_type: str
    active: bool
    created_at: datetime
    updated_at: datetime


class WebhookPayload(BaseModel):
    """Standard payload sent to webhook endpoints."""

    event: str
    timestamp: str
    data: dict[str, object]
    signature: str = ""


class WebhookDeliveryLogData(BaseModel):
    """Public delivery log for cross-module use."""

    model_config = {"from_attributes": True}

    id: UUID
    webhook_id: UUID
    status_code: int | None = None
    response_body: str = ""
    success: bool
    created_at: datetime
    error_message: str = ""
