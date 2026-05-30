"""Subscription ORM model for the billing module (BILL-002).

Tracks which plan a user is on, the Stripe subscription ID, billing
period, and auto-renew preference. One active subscription per user.

Cross-module contracts:
- Read by API-001 for plan checks
- Read by BILL-004 (customer portal)
- Integrates with StripeCustomer (BILL-001)
"""

import uuid as _uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.db.base import Base


class Subscription(Base):
    """User subscription to a BuzzReach plan."""

    __tablename__ = "subscriptions"
    __table_args__ = ({"schema": "buzzreach"},)

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True,
        default=_uuid.uuid4,
    )
    user_id: Mapped[_uuid.UUID] = mapped_column(
        ForeignKey("buzzreach.users.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    plan_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="free",
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
    )
    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    auto_renew: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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
