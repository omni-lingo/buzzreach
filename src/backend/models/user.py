"""User ORM model for the auth module (AUTH-001).

Columns: id (UUID PK), username, email, password_hash, api_key,
is_active, created_at, updated_at.

Hashing is handled by the service layer (AUTH-002), not here.
"""

import uuid as _uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.db.base import Base


def _generate_api_key() -> str:
    """Generate a prefixed API key for new users."""
    return f"bz_{_uuid.uuid4().hex}"


class User(Base):
    """BuzzReach user account."""

    __tablename__ = "users"
    __table_args__ = ({"schema": "buzzreach"},)

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True,
        default=_uuid.uuid4,
    )
    username: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(254),
        unique=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
    )
    api_key: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        default=_generate_api_key,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
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
