"""Daily usage tracking ORM model for the billing module (BILL-003).

Tracks per-user, per-day usage counters: opportunities found, API calls,
emails sent, push notifications, draft regenerations, and cost components
(Stripe, AI, search). One row per user per day — quota checks read today's
row only; historical queries scan the last 30 days.

Cross-module contracts:
- Read by API-001 for usage display
- Read by FE-001 (settings / usage bar)
- Read by PIPE-001 (quota check before scan)
- Integrates with Subscription (BILL-002)
"""

import uuid as _uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Index, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.db.base import Base


class DailyUsage(Base):
    """Per-user, per-day usage counters and cost tracking."""

    __tablename__ = "daily_usage"
    __table_args__ = (
        UniqueConstraint("user_id", "usage_date", name="uq_usage_user_date"),
        Index("ix_usage_user_date", "user_id", "usage_date"),
        {"schema": "buzzreach"},
    )

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True,
        default=_uuid.uuid4,
    )
    user_id: Mapped[_uuid.UUID] = mapped_column(
        nullable=False,
        index=True,
    )
    usage_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # --- Counters ---
    opportunities_found: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    api_calls: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    email_sent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    push_sent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    drafts_regenerated: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # --- Cost components (stored as Decimal for precision) ---
    stripe_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        default=Decimal("0"),
    )
    ai_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        default=Decimal("0"),
    )
    search_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        default=Decimal("0"),
    )

    # --- Timestamps ---
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
