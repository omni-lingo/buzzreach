"""Tests for AUTH-002: JWT service (sign, verify, refresh, password hashing).

Covers: create token, verify valid token, expired token rejected,
invalid token raises coded error, refresh issues new token,
password hash round-trip.
"""

import time
from uuid import UUID, uuid4

import pytest

from contracts.auth.jwt import JwtPayload
from src.backend.errors import AppError
from src.backend.services.auth.jwt_service import JwtService
from src.backend.settings import Settings


@pytest.fixture()
def settings() -> Settings:
    """Settings with a known test secret and short expiry."""
    return Settings(
        jwt_secret_key="test-secret-key-for-jwt",
        jwt_algorithm="HS256",
        jwt_expire_minutes=60,
    )


@pytest.fixture()
def jwt_service(settings: Settings) -> JwtService:
    """JwtService wired with test settings."""
    return JwtService(settings=settings)


class TestCreateToken:
    """JwtService.create_token() produces a signed JWT."""

    def test_returns_string(self, jwt_service: JwtService) -> None:
        token = jwt_service.create_token(user_id=uuid4())
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_has_three_segments(self, jwt_service: JwtService) -> None:
        token = jwt_service.create_token(user_id=uuid4())
        parts = token.split(".")
        assert len(parts) == 3

    def test_token_contains_user_id(self, jwt_service: JwtService) -> None:
        user_id = uuid4()
        token = jwt_service.create_token(user_id=user_id)
        decoded_id = jwt_service.verify_token(token)
        assert decoded_id == user_id


class TestVerifyToken:
    """JwtService.verify_token() validates and returns user_id."""

    def test_returns_uuid(self, jwt_service: JwtService) -> None:
        user_id = uuid4()
        token = jwt_service.create_token(user_id=user_id)
        result = jwt_service.verify_token(token)
        assert isinstance(result, UUID)
        assert result == user_id

    def test_invalid_token_raises_app_error(
        self, jwt_service: JwtService
    ) -> None:
        with pytest.raises(AppError) as exc_info:
            jwt_service.verify_token("not.a.valid.token")
        assert exc_info.value.code == "TOKEN_INVALID"

    def test_garbage_string_raises_app_error(
        self, jwt_service: JwtService
    ) -> None:
        with pytest.raises(AppError) as exc_info:
            jwt_service.verify_token("totalgarbage")
        assert exc_info.value.code == "TOKEN_INVALID"

    def test_expired_token_raises_app_error(
        self, settings: Settings
    ) -> None:
        short_settings = Settings(
            jwt_secret_key=settings.jwt_secret_key,
            jwt_algorithm=settings.jwt_algorithm,
            jwt_expire_minutes=0,
        )
        service = JwtService(settings=short_settings)
        token = service.create_token(user_id=uuid4())
        time.sleep(1)
        with pytest.raises(AppError) as exc_info:
            service.verify_token(token)
        assert exc_info.value.code == "TOKEN_EXPIRED"

    def test_wrong_secret_raises_app_error(
        self, jwt_service: JwtService
    ) -> None:
        token = jwt_service.create_token(user_id=uuid4())
        other = JwtService(
            settings=Settings(
                jwt_secret_key="different-secret",
                jwt_algorithm="HS256",
                jwt_expire_minutes=60,
            )
        )
        with pytest.raises(AppError) as exc_info:
            other.verify_token(token)
        assert exc_info.value.code == "TOKEN_INVALID"


class TestRefreshToken:
    """JwtService.refresh_token() issues a new token from a valid one."""

    def test_refresh_returns_new_token(
        self, jwt_service: JwtService
    ) -> None:
        user_id = uuid4()
        old_token = jwt_service.create_token(user_id=user_id)
        time.sleep(1)
        new_token = jwt_service.refresh_token(old_token)
        assert isinstance(new_token, str)
        assert new_token != old_token

    def test_refresh_preserves_user_id(
        self, jwt_service: JwtService
    ) -> None:
        user_id = uuid4()
        old_token = jwt_service.create_token(user_id=user_id)
        new_token = jwt_service.refresh_token(old_token)
        result = jwt_service.verify_token(new_token)
        assert result == user_id

    def test_refresh_invalid_token_raises_app_error(
        self, jwt_service: JwtService
    ) -> None:
        with pytest.raises(AppError) as exc_info:
            jwt_service.refresh_token("bad.token.here")
        assert exc_info.value.code == "TOKEN_INVALID"


class TestPasswordHashing:
    """JwtService.hash_password / verify_password bcrypt round-trip."""

    def test_hash_differs_from_plaintext(
        self, jwt_service: JwtService
    ) -> None:
        plaintext = "my-secret-password"
        hashed = jwt_service.hash_password(plaintext)
        assert hashed != plaintext

    def test_verify_correct_password(
        self, jwt_service: JwtService
    ) -> None:
        plaintext = "correct-horse-battery-staple"
        hashed = jwt_service.hash_password(plaintext)
        assert jwt_service.verify_password(plaintext, hashed) is True

    def test_verify_wrong_password(
        self, jwt_service: JwtService
    ) -> None:
        hashed = jwt_service.hash_password("right-password")
        assert jwt_service.verify_password("wrong-password", hashed) is False

    def test_hash_is_bcrypt_format(
        self, jwt_service: JwtService
    ) -> None:
        hashed = jwt_service.hash_password("test-password")
        assert hashed.startswith("$2b$")

    def test_same_password_produces_different_hashes(
        self, jwt_service: JwtService
    ) -> None:
        pw = "same-password"
        h1 = jwt_service.hash_password(pw)
        h2 = jwt_service.hash_password(pw)
        assert h1 != h2


class TestJwtPayloadContract:
    """JwtPayload DTO round-trips correctly."""

    def test_payload_fields(self) -> None:
        from datetime import UTC, datetime

        now = datetime.now(UTC)
        uid = uuid4()
        payload = JwtPayload(sub=uid, iat=now, exp=now)
        assert payload.sub == uid
        assert payload.iat == now
        assert payload.exp == now
