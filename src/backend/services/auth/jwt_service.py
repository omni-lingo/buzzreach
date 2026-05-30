"""JWT service for token signing, verification, refresh, and password hashing (AUTH-002).

Uses python-jose for JWT operations and bcrypt for password hashing.
All configuration is read from Settings (jwt_secret_key, jwt_algorithm,
jwt_expire_minutes). Errors raise AppError with specific codes
(TOKEN_INVALID, TOKEN_EXPIRED).
"""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

import bcrypt
from jose import ExpiredSignatureError, JWTError, jwt

from src.backend.errors import AppError
from src.backend.settings import Settings

log = logging.getLogger("buzzreach")


class JwtService:
    """Stateless JWT + password-hashing service.

    Injected with Settings so the secret key comes from env, never hardcoded.
    """

    def __init__(self, settings: Settings) -> None:
        self._secret = settings.jwt_secret_key
        self._algorithm = settings.jwt_algorithm
        self._expire_minutes = settings.jwt_expire_minutes

    def create_token(self, user_id: UUID) -> str:
        """Sign a JWT containing the user_id as ``sub`` claim.

        Args:
            user_id: The user's UUID to embed in the token.

        Returns:
            A signed JWT string.
        """
        now = datetime.now(UTC)
        claims = {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(minutes=self._expire_minutes),
        }
        token: str = jwt.encode(
            claims, self._secret, algorithm=self._algorithm
        )
        log.info("Token created", extra={"user_id": str(user_id)})
        return token

    def verify_token(self, token: str) -> UUID:
        """Decode and validate a JWT, returning the user_id.

        Args:
            token: The JWT string to verify.

        Returns:
            The UUID from the ``sub`` claim.

        Raises:
            AppError: TOKEN_EXPIRED if the token has expired.
            AppError: TOKEN_INVALID if the token is malformed or
                      the signature is invalid.
        """
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
            )
        except ExpiredSignatureError:
            raise AppError(
                code="TOKEN_EXPIRED",
                message="Token has expired",
            ) from None
        except JWTError:
            raise AppError(
                code="TOKEN_INVALID",
                message="Token is invalid",
            ) from None

        sub = payload.get("sub")
        if sub is None:
            raise AppError(
                code="TOKEN_INVALID",
                message="Token missing subject claim",
            )

        try:
            return UUID(sub)
        except ValueError:
            raise AppError(
                code="TOKEN_INVALID",
                message="Token subject is not a valid UUID",
            ) from None

    def refresh_token(self, old_token: str) -> str:
        """Verify an existing token and issue a fresh one.

        Args:
            old_token: The current (still valid) JWT.

        Returns:
            A new JWT with a fresh expiration.

        Raises:
            AppError: If the old token is invalid or expired.
        """
        user_id = self.verify_token(old_token)
        return self.create_token(user_id)

    @staticmethod
    def hash_password(plaintext: str) -> str:
        """Hash a plaintext password with bcrypt.

        Args:
            plaintext: The raw password string.

        Returns:
            The bcrypt hash as a string.
        """
        hashed = bcrypt.hashpw(
            plaintext.encode("utf-8"), bcrypt.gensalt()
        )
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plaintext: str, hashed: str) -> bool:
        """Check a plaintext password against a bcrypt hash.

        Args:
            plaintext: The raw password to check.
            hashed: The stored bcrypt hash.

        Returns:
            True if the password matches, False otherwise.
        """
        return bcrypt.checkpw(
            plaintext.encode("utf-8"), hashed.encode("utf-8")
        )
