"""DraftTemplate ORM model for the quality module (QUALITY-003).

Stores reusable draft templates with placeholder variables. Templates can
be global (provided by BuzzReach, user_id=NULL) or user-owned (custom).

Columns: id (UUID PK), user_id (nullable FK), name, category, description,
text (with {placeholders}), created_at, updated_at.
"""

import uuid as _uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.db.base import Base


class DraftTemplate(Base):
    """A reusable draft template with placeholder variables."""

    __tablename__ = "draft_templates"
    __table_args__ = (
        Index(
            "ix_draft_templates_category",
            "category",
        ),
        Index(
            "ix_draft_templates_user_id",
            "user_id",
        ),
        {"schema": "buzzreach"},
    )

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True,
        default=_uuid.uuid4,
    )
    user_id: Mapped[_uuid.UUID | None] = mapped_column(
        ForeignKey("buzzreach.users.id"),
        nullable=True,
        default=None,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    text: Mapped[str] = mapped_column(
        Text,
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

    @hybrid_property
    def is_global(self) -> bool:
        """True if this template is system-provided (no owner)."""
        return self.user_id is None
