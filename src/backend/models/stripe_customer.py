"""StripeCustomer ORM model for the billing module (BILL-001).

Links a BuzzReach User to a Stripe customer ID. Stores local copies of
subscription metadata so we can answer queries without hitting Stripe.
"""

import uuid as _uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.db.base import Base


class StripeCustomer(Base):
    """Maps a BuzzReach user to their Stripe customer + subscription."""

    __tablename__ = "stripe_customers"
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
    stripe_customer_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )
    plan_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )
    subscription_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="none",
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
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
