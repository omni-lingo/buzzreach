"""Team (workspace) ORM model for the admin module (ADMIN-001).

Columns: id (UUID PK), owner_id (FK to users), name, created_at.
Each team represents a workspace that groups users and their opportunities.
"""

import uuid as _uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.db.base import Base


class Team(Base):
    """A workspace that groups users and scopes opportunities."""

    __tablename__ = "teams"
    __table_args__ = ({"schema": "buzzreach"},)

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True,
        default=_uuid.uuid4,
    )
    owner_id: Mapped[_uuid.UUID] = mapped_column(
        ForeignKey("buzzreach.users.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
