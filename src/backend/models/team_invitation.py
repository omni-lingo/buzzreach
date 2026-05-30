"""TeamInvitation ORM model for the admin module (ADMIN-001).

Columns: id (UUID PK), team_id (FK), email, role, token (unique one-time),
created_at, expires_at (24 hours from creation).
"""

import uuid as _uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.db.base import Base

INVITE_EXPIRY_HOURS = 24


def _default_expires_at() -> datetime:
    """Generate an expiration timestamp 24 hours from now."""
    return datetime.now(UTC) + timedelta(hours=INVITE_EXPIRY_HOURS)


class TeamInvitation(Base):
    """A pending invitation for a user to join a team."""

    __tablename__ = "team_invitations"
    __table_args__ = ({"schema": "buzzreach"},)

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True,
        default=_uuid.uuid4,
    )
    team_id: Mapped[_uuid.UUID] = mapped_column(
        ForeignKey("buzzreach.teams.id"),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(254),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="member",
    )
    token: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        default=lambda: _uuid.uuid4().hex,
    )
    is_used: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_default_expires_at,
        nullable=False,
    )
