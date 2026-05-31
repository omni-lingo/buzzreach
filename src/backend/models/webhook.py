"""Webhook ORM model for custom integrations (EXT-003).

Stores webhook configurations per user. Each webhook listens for a
specific event type and POSTs to a user-provided HTTPS URL with
HMAC-SHA256 signed payloads.

Columns: id (UUID PK), user_id (FK), url, event_type, secret,
active, consecutive_failures, created_at, updated_at.
"""

import secrets
import uuid as _uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.db.base import Base


def _generate_secret() -> str:
    """Generate a cryptographically secure webhook secret."""
    return secrets.token_hex(32)


class Webhook(Base):
    """A user-configured webhook endpoint."""

    __tablename__ = "webhooks"
    __table_args__ = ({"schema": "buzzreach"},)

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True,
        default=_uuid.uuid4,
    )
    user_id: Mapped[_uuid.UUID] = mapped_column(
        ForeignKey("buzzreach.users.id"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    secret: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        default=_generate_secret,
    )
    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    consecutive_failures: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
