"""SearchProfile ORM model for the features module (FEAT-004).

Stores user-defined search configurations. Each profile contains keywords,
platforms, languages, and scheduling info. Users can have multiple profiles
(subject to plan limits).

Cross-module contracts:
- Read by JOB-001 (scan job fetches active profiles)
- Read by DISC-003 (discovery service runs searches)
- Managed via search API routes (FEAT-004)
"""

import uuid as _uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from src.backend.db.base import Base


class SearchProfile(Base):
    """A user-defined search profile with keywords and scheduling."""

    __tablename__ = "search_profiles"
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
    keywords: Mapped[list[Any]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    platforms: Mapped[list[Any]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    languages: Mapped[list[Any]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    schedule_times: Mapped[list[Any]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    schedule_frequency: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="daily",
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
