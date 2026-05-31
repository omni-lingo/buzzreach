"""Opportunity ORM model for the core module (CORE-003).

Each opportunity represents a discovered community thread where the user's
product could provide genuine help. Columns: id (UUID PK), niche, url, title,
source (reddit/quora/etc.), why_matched, relevance_score, draft_reply,
status (new/delivered/acted/skipped), created_at, delivered_at.
"""

import enum
import uuid as _uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.db.base import Base


class OpportunityStatus(enum.Enum):
    """Allowed status values for an opportunity."""

    NEW = "new"
    DELIVERED = "delivered"
    ACTED = "acted"
    SKIPPED = "skipped"


class Opportunity(Base):
    """A discovered community thread with a draft reply ready for the user."""

    __tablename__ = "opportunities"
    __table_args__ = ({"schema": "buzzreach"},)

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True,
        default=_uuid.uuid4,
    )
    niche: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    why_matched: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    relevance_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    draft_reply: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    edited_draft: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )
    status: Mapped[OpportunityStatus] = mapped_column(
        default=OpportunityStatus.NEW,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
