"""Signup and email verification service (ONBOARD-001).

L2 business logic — no HTTP concerns. Handles user registration,
verification token lifecycle, password hashing, and resend rate limiting.

Cross-module contracts:
- Creates User (AUTH-001) + Subscription (BILL-002)
- Uses EmailToken (ONBOARD-002)
- Returns contracts/auth/user.UserData
"""

import logging
import re
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from contracts.auth.user import UserData
from contracts.onboarding.email_verification import (
    EmailTokenResult,
    EmailTokenType,
)
from src.backend.errors import AppError
from src.backend.models.email_token import EmailToken, TokenType
from src.backend.models.subscription import Subscription
from src.backend.models.user import User
from src.backend.services.auth.jwt_service import JwtService
from src.backend.settings import Settings

log = logging.getLogger("buzzreach.onboarding")

_MIN_PASSWORD_LENGTH = 8
_PASSWORD_PATTERN = re.compile(r"^(?=.*[A-Z])(?=.*\d).{8,}$")


class AuthService:
    """Signup, verification, and resend logic.

    Args:
        session: Active SQLAlchemy session.
        settings: Application settings for token config.
    """

    def __init__(self, session: Session, settings: Settings) -> None:
        self._session = session
        self._settings = settings
        self._expiry_hours = settings.email_token_expiry_hours
        self._rate_limit = settings.email_rate_limit_per_hour

    def register_user(
        self,
        email: str,
        username: str,
        password: str,
    ) -> UserData:
        """Create a new user with a free subscription.

        Args:
            email: User email (must be unique).
            username: Display name (must be unique).
            password: Plaintext password (hashed before storage).

        Returns:
            UserData contract for the new user.

        Raises:
            AppError: PASSWORD_TOO_WEAK, EMAIL_TAKEN, or USERNAME_TAKEN.
        """
        self._validate_password(password)
        self._check_email_available(email)
        self._check_username_available(username)

        password_hash = JwtService.hash_password(password)
        user = User(
            email=email,
            username=username,
            password_hash=password_hash,
        )
        self._session.add(user)
        self._session.flush()

        sub = Subscription(user_id=user.id, plan_id="free", status="active")
        self._session.add(sub)
        self._session.commit()

        log.info("User registered", extra={"user_id": str(user.id)})
        return UserData(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
        )

    def generate_verification_token(self, user_id: UUID) -> str:
        """Create a secure verification token for the user.

        Args:
            user_id: The UUID of the user to verify.

        Returns:
            The generated token string.
        """
        token = EmailToken(
            user_id=user_id,
            email=self._get_user_email(user_id),
            token_type=TokenType.VERIFICATION,
        )
        self._session.add(token)
        self._session.commit()

        log.info(
            "Verification token created",
            extra={"user_id": str(user_id)},
        )
        return token.token

    def verify_email(self, token_str: str) -> EmailTokenResult:
        """Verify an email using the provided token.

        Marks the user as verified and the token as used.

        Args:
            token_str: The verification token from the email link.

        Returns:
            EmailTokenResult with user_id and email.

        Raises:
            AppError: TOKEN_INVALID or TOKEN_EXPIRED.
        """
        tok = self._get_valid_token(token_str)

        user = self._session.get(User, tok.user_id)
        if user is not None:
            user.email_verified = True

        tok.used = True
        self._session.commit()

        log.info(
            "Email verified",
            extra={"user_id": str(tok.user_id)},
        )
        return EmailTokenResult(
            user_id=tok.user_id,
            email=tok.email,
            token_type=EmailTokenType(tok.token_type.value),
        )

    def resend_verification(self, user_id: UUID) -> str:
        """Resend verification email (rate-limited).

        Args:
            user_id: The user requesting resend.

        Returns:
            New verification token string.

        Raises:
            AppError: RATE_LIMIT_EXCEEDED if > 3 tokens in last hour.
        """
        self._check_resend_rate_limit(user_id)
        return self.generate_verification_token(user_id)

    def _validate_password(self, password: str) -> None:
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

    def _check_email_available(self, email: str) -> None:
        """Raise if email is already registered."""
        exists = (
            self._session.query(User.id)
            .filter(func.lower(User.email) == email.lower())
            .first()
        )
        if exists:
            raise AppError(
                code="EMAIL_TAKEN",
                message="An account with this email already exists",
            )

    def _check_username_available(self, username: str) -> None:
        """Raise if username is already taken."""
        exists = (
            self._session.query(User.id)
            .filter(func.lower(User.username) == username.lower())
            .first()
        )
        if exists:
            raise AppError(
                code="USERNAME_TAKEN",
                message="This username is already taken",
            )

    def _get_user_email(self, user_id: UUID) -> str:
        """Fetch the email for a user by ID."""
        user = self._session.get(User, user_id)
        if user is None:
            raise AppError(
                code="USER_NOT_FOUND",
                message="User not found",
            )
        return user.email

    def _get_valid_token(self, token_str: str) -> EmailToken:
        """Look up and validate a verification token."""
        tok = (
            self._session.query(EmailToken)
            .filter_by(token=token_str, token_type=TokenType.VERIFICATION)
            .first()
        )
        if tok is None or tok.used:
            raise AppError(
                code="TOKEN_INVALID",
                message="Invalid or already-used token",
            )
        now = datetime.now(UTC)
        expires = tok.expires_at
        if expires.tzinfo is None:
            now = now.replace(tzinfo=None)
        if expires <= now:
            raise AppError(
                code="TOKEN_EXPIRED",
                message="Verification token has expired",
            )
        return tok

    def _check_resend_rate_limit(self, user_id: UUID) -> None:
        """Enforce max resends per hour."""
        one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
        count = (
            self._session.query(func.count(EmailToken.id))
            .filter(
                EmailToken.user_id == user_id,
                EmailToken.token_type == TokenType.VERIFICATION,
                EmailToken.created_at >= one_hour_ago,
            )
            .scalar()
        )
        if count is not None and count >= self._rate_limit:
            raise AppError(
                code="RATE_LIMIT_EXCEEDED",
                message=(
                    f"Max {self._rate_limit} verification emails "
                    f"per hour. Try again later."
                ),
            )
