"""Tests for ONBOARD-002: Email verification service.

Covers: token creation, send verification email, send password reset,
send invitation, token verification, token expiration, single-use tokens,
rate limiting (max 3 per user per hour), resend flow.
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from src.backend.errors import AppError
from src.backend.models.email_token import EmailToken, TokenType
from src.backend.models.user import User
from src.backend.services.email_service import EmailService
from src.backend.settings import Settings
from tests.conftest import make_user


@pytest.fixture()
def settings() -> Settings:
    """Settings configured for email verification tests."""
    return Settings(
        smtp_host="smtp.test.local",
        smtp_port=587,
        smtp_username="test@buzzreach.app",
        smtp_password="test-secret",
        smtp_from_email="noreply@buzzreach.app",
        app_base_url="https://app.buzzreach.test",
        email_token_expiry_hours=6,
        email_rate_limit_per_hour=3,
    )


@pytest.fixture()
def email_service(
    db_session: Session, settings: Settings,
) -> EmailService:
    """EmailService wired with test session and settings."""
    return EmailService(session=db_session, settings=settings)


@pytest.fixture()
def user(db_session: Session) -> User:
    """A persisted test user."""
    u = make_user()
    db_session.add(u)
    db_session.commit()
    return u


class TestCreateToken:
    """Token creation stores a secure, unguessable token in the DB."""

    def test_creates_verification_token(
        self, email_service: EmailService, user: User,
        db_session: Session,
    ) -> None:
        token = email_service.create_token(
            user.id, user.email, TokenType.VERIFICATION,
        )
        assert token is not None
        row = db_session.get(EmailToken, token.id)
        assert row is not None
        assert row.user_id == user.id
        assert row.token_type == TokenType.VERIFICATION
        assert not row.used

    def test_token_is_unguessable(
        self, email_service: EmailService, user: User,
    ) -> None:
        t1 = email_service.create_token(
            user.id, user.email, TokenType.VERIFICATION,
        )
        t2 = email_service.create_token(
            user.id, user.email, TokenType.VERIFICATION,
        )
        assert t1.token != t2.token
        assert len(t1.token) >= 32

    def test_token_expires_after_configured_hours(
        self, email_service: EmailService, user: User,
    ) -> None:
        token = email_service.create_token(
            user.id, user.email, TokenType.VERIFICATION,
        )
        expected_min = datetime.now(UTC) + timedelta(hours=5, minutes=59)
        expected_max = datetime.now(UTC) + timedelta(hours=6, minutes=1)
        assert expected_min <= token.expires_at <= expected_max

    def test_creates_password_reset_token(
        self, email_service: EmailService, user: User,
    ) -> None:
        token = email_service.create_token(
            user.id, user.email, TokenType.PASSWORD_RESET,
        )
        assert token.token_type == TokenType.PASSWORD_RESET


class TestVerifyToken:
    """verify_token marks the token as used and returns the user_id."""

    def test_valid_token_returns_user_id(
        self, email_service: EmailService, user: User,
    ) -> None:
        token = email_service.create_token(
            user.id, user.email, TokenType.VERIFICATION,
        )
        result = email_service.verify_token(
            token.token, TokenType.VERIFICATION,
        )
        assert result == user.id

    def test_marks_token_as_used(
        self, email_service: EmailService, user: User,
        db_session: Session,
    ) -> None:
        token = email_service.create_token(
            user.id, user.email, TokenType.VERIFICATION,
        )
        email_service.verify_token(token.token, TokenType.VERIFICATION)
        row = db_session.get(EmailToken, token.id)
        assert row is not None
        assert row.used is True

    def test_rejects_already_used_token(
        self, email_service: EmailService, user: User,
    ) -> None:
        token = email_service.create_token(
            user.id, user.email, TokenType.VERIFICATION,
        )
        email_service.verify_token(token.token, TokenType.VERIFICATION)
        with pytest.raises(AppError) as exc_info:
            email_service.verify_token(
                token.token, TokenType.VERIFICATION,
            )
        assert exc_info.value.code == "TOKEN_ALREADY_USED"

    def test_rejects_expired_token(
        self, email_service: EmailService, user: User,
        db_session: Session,
    ) -> None:
        token = email_service.create_token(
            user.id, user.email, TokenType.VERIFICATION,
        )
        token.expires_at = datetime.now(UTC) - timedelta(hours=1)
        db_session.commit()
        with pytest.raises(AppError) as exc_info:
            email_service.verify_token(
                token.token, TokenType.VERIFICATION,
            )
        assert exc_info.value.code == "TOKEN_EXPIRED"

    def test_rejects_unknown_token(
        self, email_service: EmailService,
    ) -> None:
        with pytest.raises(AppError) as exc_info:
            email_service.verify_token(
                "nonexistent-token", TokenType.VERIFICATION,
            )
        assert exc_info.value.code == "TOKEN_NOT_FOUND"

    def test_rejects_wrong_token_type(
        self, email_service: EmailService, user: User,
    ) -> None:
        token = email_service.create_token(
            user.id, user.email, TokenType.VERIFICATION,
        )
        with pytest.raises(AppError) as exc_info:
            email_service.verify_token(
                token.token, TokenType.PASSWORD_RESET,
            )
        assert exc_info.value.code == "TOKEN_NOT_FOUND"


class TestSendVerificationEmail:
    """send_verification_email creates token and sends email."""

    @patch("src.backend.services.email_service._send_smtp_email")
    def test_creates_token_then_sends(
        self, mock_send: MagicMock,
        email_service: EmailService, user: User,
        db_session: Session,
    ) -> None:
        email_service.send_verification_email(user.id, user.email)
        tokens = db_session.query(EmailToken).filter_by(
            user_id=user.id,
            token_type=TokenType.VERIFICATION,
        ).all()
        assert len(tokens) >= 1
        mock_send.assert_called_once()

    @patch("src.backend.services.email_service._send_smtp_email")
    def test_token_in_db_before_email_sent(
        self, mock_send: MagicMock,
        email_service: EmailService, user: User,
        db_session: Session,
    ) -> None:
        """Token persisted atomically before the email send attempt."""
        call_count_at_token_check = []

        def side_effect(*_args: object, **_kwargs: object) -> None:
            count = db_session.query(EmailToken).filter_by(
                user_id=user.id,
            ).count()
            call_count_at_token_check.append(count)

        mock_send.side_effect = side_effect
        email_service.send_verification_email(user.id, user.email)
        assert call_count_at_token_check[0] >= 1


class TestSendPasswordResetEmail:
    """send_password_reset_email creates a reset token and sends."""

    @patch("src.backend.services.email_service._send_smtp_email")
    def test_sends_reset_email(
        self, mock_send: MagicMock,
        email_service: EmailService, user: User,
        db_session: Session,
    ) -> None:
        email_service.send_password_reset_email(user.id, user.email)
        tokens = db_session.query(EmailToken).filter_by(
            user_id=user.id,
            token_type=TokenType.PASSWORD_RESET,
        ).all()
        assert len(tokens) == 1
        mock_send.assert_called_once()


class TestSendInvitationEmail:
    """send_invitation_email sends a team invite without a user token."""

    @patch("src.backend.services.email_service._send_smtp_email")
    def test_sends_invitation(
        self, mock_send: MagicMock,
        email_service: EmailService,
    ) -> None:
        team_id = uuid.uuid4()
        email_service.send_invitation_email(
            "invitee@example.com", team_id,
        )
        mock_send.assert_called_once()


class TestRateLimiting:
    """Max 3 emails per user per hour enforced."""

    @patch("src.backend.services.email_service._send_smtp_email")
    def test_allows_up_to_limit(
        self, mock_send: MagicMock,
        email_service: EmailService, user: User,
    ) -> None:
        for _ in range(3):
            email_service.send_verification_email(user.id, user.email)
        assert mock_send.call_count == 3

    @patch("src.backend.services.email_service._send_smtp_email")
    def test_blocks_after_limit_exceeded(
        self, mock_send: MagicMock,
        email_service: EmailService, user: User,
    ) -> None:
        for _ in range(3):
            email_service.send_verification_email(user.id, user.email)
        with pytest.raises(AppError) as exc_info:
            email_service.send_verification_email(user.id, user.email)
        assert exc_info.value.code == "EMAIL_RATE_LIMITED"

    @patch("src.backend.services.email_service._send_smtp_email")
    def test_old_tokens_dont_count(
        self, mock_send: MagicMock,
        email_service: EmailService, user: User,
        db_session: Session,
    ) -> None:
        """Tokens older than 1 hour don't count toward the rate limit."""
        for _ in range(3):
            email_service.send_verification_email(user.id, user.email)
        # Age out existing tokens
        old_time = datetime.now(UTC) - timedelta(hours=2)
        db_session.query(EmailToken).filter_by(
            user_id=user.id,
        ).update({"created_at": old_time})
        db_session.commit()
        # Should be allowed again
        email_service.send_verification_email(user.id, user.email)
        assert mock_send.call_count == 4
