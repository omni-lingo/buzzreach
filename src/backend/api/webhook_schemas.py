"""Request/response schemas for the Webhooks API (EXT-003).

WebhookResponse wraps webhook data for stable API output.
WebhookCreate and WebhookUpdate handle mutation payloads.
DeliveryLogResponse wraps delivery log entries.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class WebhookCreate(BaseModel):
    """Payload for creating a new webhook."""

    url: str = Field(
        min_length=8,
        max_length=2048,
        description="HTTPS endpoint URL",
    )
    event_type: str = Field(
        description="Event type to subscribe to",
    )


class WebhookUpdate(BaseModel):
    """Payload for updating an existing webhook."""

    url: str | None = Field(
        default=None, min_length=8, max_length=2048,
    )
    event_type: str | None = None
    active: bool | None = None


class WebhookResponse(BaseModel):
    """Public webhook representation returned by API."""

    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    url: str
    event_type: str
    secret: str
    active: bool
    consecutive_failures: int
    created_at: datetime
    updated_at: datetime


class DeliveryLogResponse(BaseModel):
    """Public delivery log entry returned by API."""

    model_config = {"from_attributes": True}

    id: UUID
    webhook_id: UUID
    status_code: int | None = None
    response_body: str = ""
    success: bool
    error_message: str = ""
    created_at: datetime
