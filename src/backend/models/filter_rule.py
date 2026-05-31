"""FilterRule ORM model for the features module (FEAT-002).

Each filter rule represents a user-defined rule for filtering opportunities.
Columns: id (UUID PK), user_id (UUID FK), name, rule_type
(regex/not/field/composite), patterns (JSON), description, enabled (bool),
created_at, updated_at.
"""

import uuid as _uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from src.backend.db.base import Base


class FilterRule(Base):
    """A user-defined filter rule for opportunity filtering."""

    __tablename__ = "filter_rules"
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
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    rule_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    patterns: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    enabled: Mapped[bool] = mapped_column(
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
