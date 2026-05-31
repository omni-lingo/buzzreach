"""OpportunityAction ORM model for post-action tracking (FEAT-003).

Tracks user actions on opportunities: viewed, copied, posted, archived.
Each row records one action with an optional posted_url for reply links.

Composite index on (user_id, opportunity_id) for fast per-user queries
and (user_id, action_type, created_at) for analytics funnel aggregation.
"""

import uuid as _uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.db.base import Base


class OpportunityAction(Base):
    """A tracked user action on an opportunity."""

    __tablename__ = "opportunity_actions"
    __table_args__ = (
        Index(
            "ix_opp_actions_user_opp",
            "user_id",
            "opportunity_id",
        ),
        Index(
            "ix_opp_actions_user_type_created",
            "user_id",
            "action_type",
            "created_at",
        ),
        {"schema": "buzzreach"},
    )

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True,
        default=_uuid.uuid4,
    )
    opportunity_id: Mapped[_uuid.UUID] = mapped_column(
        nullable=False,
    )
    user_id: Mapped[_uuid.UUID] = mapped_column(
        nullable=False,
    )
    action_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    posted_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
