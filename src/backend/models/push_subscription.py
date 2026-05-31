"""PushSubscription ORM model for the mobile module (MOBILE-002).

Stores device push tokens for iOS and Android devices. Each user
can have multiple active tokens (one per device). Stale tokens
are deactivated via Expo feedback API or manual unregister.

Cross-module contracts:
- Read by push_service (MOBILE-002) for notification delivery
- Read by JOB-001 for opportunity notification dispatch
- Written by push API routes (MOBILE-002)
"""

import uuid as _uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.db.base import Base


class PushSubscription(Base):
    """Device push notification token for a user."""

    __tablename__ = "push_subscriptions"
    __table_args__ = (
        Index(
            "ix_push_user_active",
            "user_id",
            "is_active",
        ),
        Index(
            "ix_push_device_token",
            "device_token",
        ),
        {"schema": "buzzreach"},
    )

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True,
        default=_uuid.uuid4,
    )
    user_id: Mapped[_uuid.UUID] = mapped_column(
        ForeignKey("buzzreach.users.id"),
        nullable=False,
        index=True,
    )
    device_token: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    platform: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
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
