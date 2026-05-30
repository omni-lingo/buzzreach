"""SeenUrl ORM model for the core module (CORE-002).

Dedup table tracking our own actions: which URLs have been seen,
in which niche, what angle was covered, and who it was shown to.
Columns: id (UUID PK), url, niche, angle_covered, shown_to, created_at.

Unique constraint on (url, niche) prevents duplicate processing.
"""

import uuid as _uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.db.base import Base


class SeenUrl(Base):
    """Record of a URL already seen/processed for a given niche."""

    __tablename__ = "seen_urls"
    __table_args__ = (
        UniqueConstraint("url", "niche", name="uq_seen_urls_url_niche"),
        {"schema": "buzzreach"},
    )

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True,
        default=_uuid.uuid4,
    )
    url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )
    niche: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    angle_covered: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )
    shown_to: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
