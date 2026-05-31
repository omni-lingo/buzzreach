"""Cross-module contract for email verification (ONBOARD-002).

This contract defines the interface that other modules (ONBOARD-001 signup,
ONBOARD-004 password reset) use to trigger verification and reset emails.
"""

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class EmailTokenType(StrEnum):
    """Token type values matching the ORM model's TokenType."""

    VERIFICATION = "verification"
    PASSWORD_RESET = "password_reset"


class EmailTokenResult(BaseModel):
    """Result of token verification — returned to callers."""

    user_id: UUID
    email: str
    token_type: EmailTokenType
