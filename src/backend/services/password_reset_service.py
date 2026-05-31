"""Password reset service (ONBOARD-004).

L2 business logic — no HTTP concerns. Handles password reset token
creation, validation, and password update with session invalidation.

Cross-module contracts:
- Uses EmailToken (ONBOARD-002)
- Uses User (AUTH-001) for password_hash and api_key
- Shares password validation with AuthService (ONBOARD-001)
"""

import logging
import re
import uuid as _uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.backend.errors import AppError
from src.backend.models.email_token import EmailToken, TokenType
from src.backend.models.user import User
from src.backend.services.auth.jwt_service import JwtService
from src.backend.settings import Settings

log = logging.getLogger("buzzreach.onboarding")

_MIN_PASSWORD_LENGTH = 8
_PASSWORD_PATTERN = re.compile(r"^(?=.*[A-Z])(?=.*\d).{8,}$")


class PasswordResetService:
    """Password reset token creation and password update.

    Args:
        session: Active SQLAlchemy session.
        settings: Application settings for token config.
    """

    def __init__(self, session: Session, settings: Settings) -> None:
        self._session = session
        self._rate_limit = settings.email_rate_limit_per_hour

    def request_password_reset(self, email: str) -> None:
        """Initiate a password reset for the given email.

        Silently succeeds if the email is not registered (security).

        Args:
            email: The email address to send a reset token to.

        Raises:
            AppError: RESET_RATE_LIMITED if > 3 requests in last hour.
        """
        user = (
            self._session.query(User)
            .filter(func.lower(User.email) == email.lower())
            .first()
        )
        if user is None:
            return

        self._check_reset_rate_limit(user.id)
        token = EmailToken(
            user_id=user.id,
            email=user.email,
            token_type=TokenType.PASSWORD_RESET,
        )
        self._session.add(token)
        self._session.commit()
        log.info(
            "Password reset token created",
            extra={"user_id": str(user.id)},
        )

    def reset_password(self, token_str: str, new_password: str) -> None:
        """Reset a user's password using a valid reset token.

        Validates password strength, verifies the token, hashes and
        saves the new password, and rotates the api_key to invalidate
        existing sessions.

        Args:
            token_str: The reset token from the email link.
            new_password: The new plaintext password.

        Raises:
            AppError: PASSWORD_TOO_WEAK, TOKEN_INVALID, or TOKEN_EXPIRED.
        """
        _validate_password(new_password)
        tok = self._get_valid_reset_token(token_str)

        user = self._session.get(User, tok.user_id)
        if user is None:
            raise AppError(code="USER_NOT_FOUND", message="User not found")

        user.password_hash = JwtService.hash_password(new_password)
        user.api_key = f"bz_{_uuid.uuid4().hex}"
        tok.used = True
        self._session.commit()
        log.info(
            "Password reset completed",
            extra={"user_id": str(user.id)},
        )

    def _get_valid_reset_token(self, token_str: str) -> EmailToken:
        """Look up and validate a password reset token."""
        tok = (
            self._session.query(EmailToken)
            .filter_by(
                token=token_str, token_type=TokenType.PASSWORD_RESET,
            )
            .first()
        )
        if tok is None or tok.used:
            raise AppError(
                code="TOKEN_INVALID",
                message="Invalid or already-used reset token",
            )
        now = datetime.now(UTC)
        expires = tok.expires_at
        if expires.tzinfo is None:
            now = now.replace(tzinfo=None)
        if expires <= now:
            raise AppError(
                code="TOKEN_EXPIRED",
                message="Password reset token has expired",
            )
        return tok

    def _check_reset_rate_limit(self, user_id: _uuid.UUID) -> None:
        """Enforce max password reset requests per hour."""
        one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
        count = (
            self._session.query(func.count(EmailToken.id))
            .filter(
                EmailToken.user_id == user_id,
                EmailToken.token_type == TokenType.PASSWORD_RESET,
                EmailToken.created_at >= one_hour_ago,
            )
            .scalar()
        )
        if count is not None and count >= self._rate_limit:
            raise AppError(
                code="RESET_RATE_LIMITED",
                message=(
                    f"Max {self._rate_limit} password reset requests "
                    f"per hour. Try again later."
                ),
            )


def _validate_password(password: str) -> None:
    """Enforce password strength requirements."""
    if (
        len(password) < _MIN_PASSWORD_LENGTH
        or not _PASSWORD_PATTERN.match(password)
    ):
        raise AppError(
            code="PASSWORD_TOO_WEAK",
            message=(
                "Password must be at least 8 characters with "
                "an uppercase letter and a number"
            ),
        )
