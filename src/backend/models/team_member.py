"""TeamMember ORM model for the admin module (ADMIN-001).

Columns: id (UUID PK), team_id (FK), user_id (FK), role (enum),
invited_at, joined_at, created_at.
Unique constraint on (team_id, user_id) prevents duplicate memberships.
"""

import enum
import uuid as _uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.db.base import Base


class TeamRole(enum.Enum):
    """Allowed roles for a team member."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class TeamMember(Base):
    """A user's membership in a team with a specific role."""

    __tablename__ = "team_members"
    __table_args__ = (
        UniqueConstraint(
            "team_id", "user_id", name="uq_team_members_team_user"
        ),
        {"schema": "buzzreach"},
    )

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True,
        default=_uuid.uuid4,
    )
    team_id: Mapped[_uuid.UUID] = mapped_column(
        ForeignKey("buzzreach.teams.id"),
        nullable=False,
    )
    user_id: Mapped[_uuid.UUID] = mapped_column(
        ForeignKey("buzzreach.users.id"),
        nullable=False,
    )
    role: Mapped[TeamRole] = mapped_column(
        Enum(TeamRole, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=TeamRole.MEMBER,
    )
    invited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    joined_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
