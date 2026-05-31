"""Email verification service for the onboarding module (ONBOARD-002).

Handles token creation, verification, and email dispatch for:
- Email verification after signup
- Password reset
- Team invitations

Rate limiting: max N emails per user per hour (configurable via settings).
Tokens are single-use and expire after a configurable number of hours.
"""

import logging
import smtplib
from datetime import UTC, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Protocol
from uuid import UUID

from sqlalchemy.orm import Session

from src.backend.errors import AppError
from src.backend.models.email_token import EmailToken, TokenType
from src.backend.services.email_templates import (
    invitation_email,
    password_reset_email,
    verification_email,
)

log = logging.getLogger("buzzreach")


class _Settings(Protocol):
    """Subset of Settings fields used by the email service."""

    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    app_base_url: str
    email_token_expiry_hours: int
    email_rate_limit_per_hour: int


class EmailService:
    """Service for sending verification, reset, and invitation emails.

    Args:
        session: SQLAlchemy session for token persistence.
        settings: Application settings with SMTP and token config.
    """

    def __init__(self, session: Session, settings: _Settings) -> None:
        self._session = session
        self._settings = settings

    def create_token(
        self,
        user_id: UUID,
        email: str,
        token_type: TokenType,
    ) -> EmailToken:
        """Create and persist a new email token.

        Args:
            user_id: The user this token belongs to.
            email: The email address for this token.
            token_type: verification or password_reset.

        Returns:
            The persisted EmailToken row.
        """
        token = EmailToken(
            user_id=user_id,
            email=email,
            token_type=token_type,
        )
        self._session.add(token)
        self._session.commit()
        log.info(
            "Email token created",
            extra={
                "user_id": str(user_id),
                "token_type": token_type.value,
            },
        )
        return token

    def verify_token(
        self, token_value: str, token_type: TokenType,
    ) -> UUID:
        """Verify a token and mark it as used.

        Args:
            token_value: The raw token string from the email link.
            token_type: Expected token type (verification/password_reset).

        Returns:
            The user_id associated with the token.

        Raises:
            AppError: If the token is not found, expired, or already used.
        """
        row = self._session.query(EmailToken).filter_by(
            token=token_value,
            token_type=token_type,
        ).first()

        if row is None:
            raise AppError(
                code="TOKEN_NOT_FOUND",
                message="Invalid or unknown token",
            )
        if row.used:
            raise AppError(
                code="TOKEN_ALREADY_USED",
                message="This token has already been used",
            )
        if row.expires_at <= datetime.now(UTC):
            raise AppError(
                code="TOKEN_EXPIRED",
                message="This token has expired",
            )

        row.used = True
        self._session.commit()
        log.info(
            "Email token verified",
            extra={
                "user_id": str(row.user_id),
                "token_type": token_type.value,
            },
        )
        return row.user_id

    def send_verification_email(
        self, user_id: UUID, email: str,
    ) -> None:
        """Send a verification email with a unique token link.

        Creates the token in DB *before* attempting to send the email
        (atomicity requirement). Enforces rate limiting.

        Args:
            user_id: The user to send verification to.
            email: The email address to send to.

        Raises:
            AppError: If rate limit is exceeded.
        """
        self._enforce_rate_limit(user_id)
        token = self.create_token(user_id, email, TokenType.VERIFICATION)
        url = self._build_url("/verify-email", token.token)
        subject, html, text = verification_email(url)
        _send_smtp_email(self._settings, email, subject, html, text)

    def send_password_reset_email(
        self, user_id: UUID, email: str,
    ) -> None:
        """Send a password reset email with a unique token link.

        Args:
            user_id: The user requesting the reset.
            email: The email address to send to.

        Raises:
            AppError: If rate limit is exceeded.
        """
        self._enforce_rate_limit(user_id)
        token = self.create_token(
            user_id, email, TokenType.PASSWORD_RESET,
        )
        url = self._build_url("/reset-password", token.token)
        subject, html, text = password_reset_email(url)
        _send_smtp_email(self._settings, email, subject, html, text)

    def send_invitation_email(
        self, email: str, team_id: UUID,
    ) -> None:
        """Send a team invitation email.

        Invitations don't create an EmailToken (they use
        TeamInvitation tokens from ADMIN-001).

        Args:
            email: The invitee's email address.
            team_id: The team the user is invited to.
        """
        invite_url = (
            f"{self._settings.app_base_url}"
            f"/accept-invite?team={team_id}"
        )
        subject, html, text = invitation_email(
            invite_url, team_name="Your Team",
        )
        _send_smtp_email(self._settings, email, subject, html, text)
        log.info(
            "Invitation email sent",
            extra={"email": email, "team_id": str(team_id)},
        )

    def _enforce_rate_limit(self, user_id: UUID) -> None:
        """Raise if user has exceeded email rate limit in the past hour."""
        one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
        recent_count = self._session.query(EmailToken).filter(
            EmailToken.user_id == user_id,
            EmailToken.created_at >= one_hour_ago,
        ).count()

        limit = self._settings.email_rate_limit_per_hour
        if recent_count >= limit:
            log.info(
                "Email rate limit exceeded",
                extra={
                    "user_id": str(user_id),
                    "recent_count": recent_count,
                    "limit": limit,
                },
            )
            raise AppError(
                code="EMAIL_RATE_LIMITED",
                message=f"Max {limit} emails per hour exceeded",
            )

    def _build_url(self, path: str, token: str) -> str:
        """Build a full verification/reset URL."""
        return f"{self._settings.app_base_url}{path}?token={token}"


def _send_smtp_email(
    settings: _Settings,
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str,
) -> None:
    """Send an email via SMTP.

    Args:
        settings: SMTP configuration.
        to_email: Recipient email address.
        subject: Email subject line.
        html_body: HTML body content.
        text_body: Plain text body content.
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from_email
    msg["To"] = to_email
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)

    log.info("Email sent", extra={"to": to_email, "subject": subject})
