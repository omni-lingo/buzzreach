"""FastAPI authentication dependency (API-001).

Validates JWT bearer tokens and returns UserData. Raises 401 on
invalid or missing tokens. Used as ``Depends(get_current_user)``
on protected endpoints.
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from contracts.auth.user import UserData
from src.backend.db.session import get_session
from src.backend.errors import AppError
from src.backend.models.user import User
from src.backend.services.auth.jwt_service import JwtService
from src.backend.settings import Settings

log = logging.getLogger("buzzreach.api.auth")

_bearer_scheme = HTTPBearer(auto_error=False)


def _get_jwt_service() -> JwtService:
    """Build a JwtService from current Settings."""
    return JwtService(Settings())


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer_scheme),
    ],
    session: Annotated[Session, Depends(get_session)],
    jwt_service: Annotated[JwtService, Depends(_get_jwt_service)],
) -> UserData:
    """Extract and validate user from JWT bearer token.

    Returns:
        UserData for the authenticated user.

    Raises:
        HTTPException: 401 if token is missing, invalid, or user not found.
    """
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail={"error_code": "AUTH_REQUIRED", "message": "Missing bearer token"},
        )

    try:
        user_id: UUID = jwt_service.verify_token(credentials.credentials)
    except AppError:
        raise HTTPException(
            status_code=401,
            detail={"error_code": "TOKEN_INVALID", "message": "Invalid or expired token"},
        ) from None

    user = session.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail={"error_code": "USER_NOT_FOUND", "message": "User not found or inactive"},
        )

    log.info("User authenticated", extra={"user_id": str(user_id)})
    return UserData(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
    )
