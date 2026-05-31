"""Tests for ONBOARD-004 password reset & account recovery.

Covers: request_password_reset (forgot), reset_password (new password),
invalid token, expired token, used token, rate limiting, password validation,
and session invalidation via api_key rotation.
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from src.backend.errors import AppError
from src.backend.models.email_token import EmailToken, TokenType
from src.backend.models.user import User
from src.backend.services.auth.jwt_service import JwtService
from src.backend.services.auth_service import AuthService
from src.backend.services.password_reset_service import PasswordResetService
from src.backend.settings import Settings

_TEST_SETTINGS = {
    "jwt_secret_key": "test-secret",
    "email_token_expiry_hours": 6,
    "email_rate_limit_per_hour": 3,
    "app_base_url": "http://localhost:8000",
    "smtp_host": "",
}
_STRONG_PW = "StrongP4ss!"
_NEW_PW = "NewStr0ng!Pw"


def _auth_svc(db_session: Session) -> AuthService:
    return AuthService(session=db_session, settings=Settings(**_TEST_SETTINGS))


def _reset_svc(db_session: Session) -> PasswordResetService:
    return PasswordResetService(
        session=db_session, settings=Settings(**_TEST_SETTINGS),
    )


def _register(db_session: Session, email: str, username: str) -> object:
    svc = _auth_svc(db_session)
    return svc.register_user(email=email, username=username, password=_STRONG_PW)


def _create_reset_token(
    svc: PasswordResetService, db_session: Session, email: str,
) -> str:
    """Request a password reset and return the raw token string."""
    svc.request_password_reset(email)
    tok = (
        db_session.query(EmailToken)
        .filter_by(email=email, token_type=TokenType.PASSWORD_RESET)
        .order_by(EmailToken.created_at.desc())
        .first()
    )
    assert tok is not None
    return tok.token


def test_request_reset_creates_token(db_session: Session) -> None:
    _register(db_session, "reset@example.com", "resetuser")
    svc = _reset_svc(db_session)
    svc.request_password_reset("reset@example.com")

    tok = (
        db_session.query(EmailToken)
        .filter_by(
            email="reset@example.com",
            token_type=TokenType.PASSWORD_RESET,
        )
        .first()
    )
    assert tok is not None
    assert tok.used is False


def test_request_reset_unknown_email_no_error(db_session: Session) -> None:
    """No error revealed for non-existent emails (security)."""
    svc = _reset_svc(db_session)
    svc.request_password_reset("nobody@example.com")


def test_reset_password_succeeds(db_session: Session) -> None:
    user = _register(db_session, "pw@example.com", "pwuser")
    svc = _reset_svc(db_session)
    token_str = _create_reset_token(svc, db_session, "pw@example.com")

    svc.reset_password(token_str, _NEW_PW)

    db_user = db_session.get(User, user.id)
    assert db_user is not None
    assert JwtService.verify_password(_NEW_PW, db_user.password_hash)


def test_reset_password_marks_token_used(db_session: Session) -> None:
    _register(db_session, "used@example.com", "useduser")
    svc = _reset_svc(db_session)
    token_str = _create_reset_token(svc, db_session, "used@example.com")

    svc.reset_password(token_str, _NEW_PW)

    tok = db_session.query(EmailToken).filter_by(token=token_str).first()
    assert tok is not None
    assert tok.used is True


def test_reset_password_invalid_token(db_session: Session) -> None:
    svc = _reset_svc(db_session)
    with pytest.raises(AppError) as exc_info:
        svc.reset_password("nonexistent-token", _NEW_PW)
    assert exc_info.value.code == "TOKEN_INVALID"


def test_reset_password_expired_token(db_session: Session) -> None:
    _register(db_session, "exp@example.com", "expuser")
    svc = _reset_svc(db_session)
    token_str = _create_reset_token(svc, db_session, "exp@example.com")

    tok = db_session.query(EmailToken).filter_by(token=token_str).first()
    assert tok is not None
    tok.expires_at = datetime.now(UTC) - timedelta(hours=1)
    db_session.commit()

    with pytest.raises(AppError) as exc_info:
        svc.reset_password(token_str, _NEW_PW)
    assert exc_info.value.code == "TOKEN_EXPIRED"


def test_reset_password_already_used_token(db_session: Session) -> None:
    _register(db_session, "once@example.com", "onceuser")
    svc = _reset_svc(db_session)
    token_str = _create_reset_token(svc, db_session, "once@example.com")

    svc.reset_password(token_str, _NEW_PW)

    with pytest.raises(AppError) as exc_info:
        svc.reset_password(token_str, "AnotherP4ss!")
    assert exc_info.value.code == "TOKEN_INVALID"


def test_reset_password_weak_password_rejected(db_session: Session) -> None:
    _register(db_session, "weak@example.com", "weakuser")
    svc = _reset_svc(db_session)
    token_str = _create_reset_token(svc, db_session, "weak@example.com")

    with pytest.raises(AppError) as exc_info:
        svc.reset_password(token_str, "short")
    assert exc_info.value.code == "PASSWORD_TOO_WEAK"


def test_reset_password_no_uppercase_rejected(db_session: Session) -> None:
    _register(db_session, "noupper@example.com", "noupperuser")
    svc = _reset_svc(db_session)
    token_str = _create_reset_token(svc, db_session, "noupper@example.com")

    with pytest.raises(AppError) as exc_info:
        svc.reset_password(token_str, "alllowercase1")
    assert exc_info.value.code == "PASSWORD_TOO_WEAK"


def test_reset_password_no_number_rejected(db_session: Session) -> None:
    _register(db_session, "nonum@example.com", "nonumuser")
    svc = _reset_svc(db_session)
    token_str = _create_reset_token(svc, db_session, "nonum@example.com")

    with pytest.raises(AppError) as exc_info:
        svc.reset_password(token_str, "NoNumbersHere")
    assert exc_info.value.code == "PASSWORD_TOO_WEAK"


def test_reset_invalidates_sessions(db_session: Session) -> None:
    """After reset, old api_key is rotated (invalidates sessions)."""
    user = _register(db_session, "sess@example.com", "sessuser")
    old_key = db_session.get(User, user.id).api_key

    svc = _reset_svc(db_session)
    token_str = _create_reset_token(svc, db_session, "sess@example.com")
    svc.reset_password(token_str, _NEW_PW)

    db_session.expire_all()
    new_key = db_session.get(User, user.id).api_key
    assert new_key != old_key


def test_reset_rate_limited(db_session: Session) -> None:
    """Max 3 reset requests per hour per user."""
    _register(db_session, "rate@example.com", "rateuser")
    svc = _reset_svc(db_session)

    for _ in range(3):
        svc.request_password_reset("rate@example.com")

    with pytest.raises(AppError) as exc_info:
        svc.request_password_reset("rate@example.com")
    assert exc_info.value.code == "RESET_RATE_LIMITED"
