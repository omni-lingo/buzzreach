"""EmailToken ORM model for the onboarding module (ONBOARD-002).

Columns: id (UUID PK), user_id (FK), email, token (secure random, unique),
token_type (verification/password_reset), used (bool), created_at,
expires_at (6 hours from creation).
"""

import secrets
import uuid as _uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.db.base import Base

TOKEN_EXPIRY_HOURS = 6
TOKEN_BYTE_LENGTH = 32


class TokenType(StrEnum):
    """Allowed email token types."""

    VERIFICATION = "verification"
    PASSWORD_RESET = "password_reset"


def _default_expires_at() -> datetime:
    """Generate an expiration timestamp 6 hours from now."""
    return datetime.now(UTC) + timedelta(hours=TOKEN_EXPIRY_HOURS)


def _generate_secure_token() -> str:
    """Generate a cryptographically secure, URL-safe token."""
    return secrets.token_urlsafe(TOKEN_BYTE_LENGTH)


class EmailToken(Base):
    """A one-time email verification or password-reset token."""

    __tablename__ = "email_tokens"
    __table_args__ = ({"schema": "buzzreach"},)

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True,
        default=_uuid.uuid4,
    )
    user_id: Mapped[_uuid.UUID] = mapped_column(
        ForeignKey("buzzreach.users.id"),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(254),
        nullable=False,
    )
    token: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        default=_generate_secure_token,
    )
    token_type: Mapped[TokenType] = mapped_column(
        Enum(TokenType, name="token_type_enum"),
        nullable=False,
    )
    used: Mapped[bool] = mapped_column(
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
