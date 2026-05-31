"""Tests for ONBOARD-001 signup / registration flow.

Covers: register_user, generate_verification_token, verify_email,
resend_verification, duplicate rejection, token expiry, rate limiting.
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from src.backend.errors import AppError
from src.backend.models.email_token import EmailToken, TokenType
from src.backend.models.subscription import Subscription
from src.backend.models.user import User
from src.backend.services.auth.jwt_service import JwtService
from src.backend.services.auth_service import AuthService
from src.backend.settings import Settings

_TEST_SETTINGS = {
    "jwt_secret_key": "test-secret",
    "email_token_expiry_hours": 6,
    "email_rate_limit_per_hour": 3,
    "app_base_url": "http://localhost:8000",
    "smtp_host": "",
}
_STRONG_PW = "StrongP4ss!"


def _svc(db_session: Session) -> AuthService:
    return AuthService(session=db_session, settings=Settings(**_TEST_SETTINGS))


def _register(svc: AuthService, email: str, username: str, pw: str = _STRONG_PW):
    return svc.register_user(email=email, username=username, password=pw)


def test_register_creates_user_and_subscription(db_session: Session) -> None:
    svc = _svc(db_session)
    user = _register(svc, "alice@example.com", "alice")
    assert user.email == "alice@example.com"
    assert user.username == "alice"
    assert user.is_active is True

    db_user = db_session.get(User, user.id)
    assert db_user is not None
    assert db_user.password_hash != _STRONG_PW

    sub = db_session.query(Subscription).filter_by(user_id=user.id).one_or_none()
    assert sub is not None
    assert sub.plan_id == "free"
    assert sub.status == "active"


def test_duplicate_email_rejected(db_session: Session) -> None:
    svc = _svc(db_session)
    _register(svc, "dup@example.com", "user1")
    with pytest.raises(AppError) as exc_info:
        _register(svc, "dup@example.com", "user2")
    assert exc_info.value.code == "EMAIL_TAKEN"


def test_duplicate_username_rejected(db_session: Session) -> None:
    svc = _svc(db_session)
    _register(svc, "a@example.com", "samename")
    with pytest.raises(AppError) as exc_info:
        _register(svc, "b@example.com", "samename")
    assert exc_info.value.code == "USERNAME_TAKEN"


def test_email_verified_defaults_false(db_session: Session) -> None:
    svc = _svc(db_session)
    user = _register(svc, "new@example.com", "newuser")
    db_user = db_session.get(User, user.id)
    assert db_user is not None
    assert db_user.email_verified is False


def test_generate_verification_token(db_session: Session) -> None:
    svc = _svc(db_session)
    user = _register(svc, "tok@example.com", "tokuser")
    token_str = svc.generate_verification_token(user.id)
    assert isinstance(token_str, str) and len(token_str) > 10

    tok = (
        db_session.query(EmailToken)
        .filter_by(user_id=user.id, token_type=TokenType.VERIFICATION)
        .first()
    )
    assert tok is not None
    assert tok.token == token_str and tok.used is False
    now = datetime.now(UTC).replace(tzinfo=None)
    expires = tok.expires_at.replace(tzinfo=None) if tok.expires_at else None
    assert expires is not None and expires > now


def test_verify_email_marks_user_verified(db_session: Session) -> None:
    svc = _svc(db_session)
    user = _register(svc, "ver@example.com", "veruser")
    token_str = svc.generate_verification_token(user.id)
    result = svc.verify_email(token_str)

    assert result.user_id == user.id
    db_user = db_session.get(User, user.id)
    assert db_user is not None and db_user.email_verified is True

    tok = db_session.query(EmailToken).filter_by(token=token_str).first()
    assert tok is not None and tok.used is True


def test_verify_email_token_one_time_use(db_session: Session) -> None:
    svc = _svc(db_session)
    user = _register(svc, "once@example.com", "onceuser")
    token_str = svc.generate_verification_token(user.id)
    svc.verify_email(token_str)
    with pytest.raises(AppError) as exc_info:
        svc.verify_email(token_str)
    assert exc_info.value.code == "TOKEN_INVALID"


def test_verify_email_expired_token_rejected(db_session: Session) -> None:
    svc = _svc(db_session)
    user = _register(svc, "exp@example.com", "expuser")
    token_str = svc.generate_verification_token(user.id)
    tok = db_session.query(EmailToken).filter_by(token=token_str).first()
    assert tok is not None
    tok.expires_at = datetime.now(UTC) - timedelta(hours=1)
    db_session.commit()

    with pytest.raises(AppError) as exc_info:
        svc.verify_email(token_str)
    assert exc_info.value.code == "TOKEN_EXPIRED"


def test_verify_email_invalid_token_rejected(db_session: Session) -> None:
    svc = _svc(db_session)
    with pytest.raises(AppError) as exc_info:
        svc.verify_email("nonexistent-token-xyz")
    assert exc_info.value.code == "TOKEN_INVALID"


def test_resend_verification_succeeds(db_session: Session) -> None:
    svc = _svc(db_session)
    user = _register(svc, "resend@example.com", "resenduser")
    token = svc.resend_verification(user.id)
    assert isinstance(token, str) and len(token) > 10


def test_resend_verification_rate_limited(db_session: Session) -> None:
    svc = _svc(db_session)
    user = _register(svc, "rate@example.com", "rateuser")
    for _ in range(3):
        svc.resend_verification(user.id)
    with pytest.raises(AppError) as exc_info:
        svc.resend_verification(user.id)
    assert exc_info.value.code == "RATE_LIMIT_EXCEEDED"


def test_password_is_hashed_on_register(db_session: Session) -> None:
    svc = _svc(db_session)
    user = _register(svc, "hash@example.com", "hashuser")
    db_user = db_session.get(User, user.id)
    assert db_user is not None
    assert db_user.password_hash != _STRONG_PW
    assert JwtService.verify_password(_STRONG_PW, db_user.password_hash)


def test_weak_password_rejected(db_session: Session) -> None:
    svc = _svc(db_session)
    with pytest.raises(AppError) as exc_info:
        _register(svc, "weak@example.com", "weakuser", pw="short")
    assert exc_info.value.code == "PASSWORD_TOO_WEAK"


def test_password_without_uppercase_rejected(db_session: Session) -> None:
    svc = _svc(db_session)
    with pytest.raises(AppError) as exc_info:
        _register(svc, "weak2@example.com", "weak2user", pw="alllowercase1")
    assert exc_info.value.code == "PASSWORD_TOO_WEAK"


def test_password_without_number_rejected(db_session: Session) -> None:
    svc = _svc(db_session)
    with pytest.raises(AppError) as exc_info:
        _register(svc, "weak3@example.com", "weak3user", pw="NoNumbersHere")
    assert exc_info.value.code == "PASSWORD_TOO_WEAK"
