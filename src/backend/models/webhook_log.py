"""Webhook delivery log ORM model (EXT-003).

Stores the last 100 delivery attempts per webhook for debugging.
Each log records the HTTP status code, response body, and whether
the delivery was successful.

Columns: id (UUID PK), webhook_id (FK), status_code, response_body,
success, error_message, created_at.
"""

import uuid as _uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.db.base import Base


class WebhookDeliveryLog(Base):
    """A single webhook delivery attempt record."""

    __tablename__ = "webhook_delivery_logs"
    __table_args__ = ({"schema": "buzzreach"},)

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True,
        default=_uuid.uuid4,
    )
    webhook_id: Mapped[_uuid.UUID] = mapped_column(
        ForeignKey("buzzreach.webhooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    response_body: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )
    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
    error_message: Mapped[str] = mapped_column(
        String(1000),
        default="",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
