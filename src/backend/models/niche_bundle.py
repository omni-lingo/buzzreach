"""NicheBundle ORM model for the quality module (QUALITY-004).

Stores pre-configured niche profile bundles with keywords, platforms,
tone guides, and draft templates. Bundles are system-provided and
can be applied to create search profiles (FEAT-004).

Cross-module contracts:
- Read by niche bundle API routes (QUALITY-004)
- Creates SearchProfile on apply (FEAT-004)
- Templates reference QUALITY-003 format
"""

import uuid as _uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from src.backend.db.base import Base


class NicheBundle(Base):
    """A pre-configured niche profile bundle."""

    __tablename__ = "niche_bundles"
    __table_args__ = ({"schema": "buzzreach"},)

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True,
        default=_uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
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
    tone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    tone_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    templates: Mapped[list[Any]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    icon: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="box",
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
