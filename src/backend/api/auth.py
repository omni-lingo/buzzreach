"""Auth API routes for signup and email verification (ONBOARD-001).

POST /api/v1/auth/signup — register new user
GET  /api/v1/auth/verify — verify email via token
POST /api/v1/auth/resend-verification — resend verification email

All routes are public (no JWT required). Rate limiting is applied
per-IP via the shared rate limit middleware.
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from src.backend.db.session import get_session
from src.backend.errors import AppError
from src.backend.services.auth_service import AuthService
from src.backend.settings import Settings

log = logging.getLogger("buzzreach.api.auth")

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# --- Request / Response schemas ---


class SignupRequest(BaseModel):
    """Signup request body."""

    email: EmailStr
    username: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=8, max_length=128)


class SignupResponse(BaseModel):
    """Signup success response."""

    user_id: UUID
    username: str
    email: str
    message: str


class VerifyResponse(BaseModel):
    """Email verification success response."""

    user_id: UUID
    email: str
    verified: bool


class ResendRequest(BaseModel):
    """Resend verification request body."""

    email: str = Field(max_length=254)


class ResendResponse(BaseModel):
    """Resend verification success response."""

    message: str


class ErrorResponse(BaseModel):
    """Standard error response body."""

    error_code: str
    message: str


# --- Helpers ---


def _get_settings() -> Settings:
    """Return application settings."""
    return Settings()


def _build_auth_service(
    session: Session,
    settings: Settings,
) -> AuthService:
    """Build AuthService from session and settings."""
    return AuthService(session=session, settings=settings)


# --- Routes ---


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=201,
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def signup(
    body: SignupRequest,
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(_get_settings)],
) -> SignupResponse:
    """Register a new user account.

    Creates a user with a free subscription and generates a
    verification token. The verification email should be sent
    by the caller or a background task.
    """
    svc = _build_auth_service(session, settings)
    try:
        user = svc.register_user(
            email=body.email,
            username=body.username,
            password=body.password,
        )
    except AppError as exc:
        status = _error_status(exc.code)
        raise HTTPException(
            status_code=status,
            detail={"error_code": exc.code, "message": exc.message},
        ) from None

    try:
        svc.generate_verification_token(user.id)
    except AppError:
        log.warning(
            "Token generation failed after signup",
            extra={"user_id": str(user.id)},
        )

    log.info("Signup completed", extra={"user_id": str(user.id)})
    return SignupResponse(
        user_id=user.id,
        username=user.username,
        email=user.email,
        message="Account created. Check your email for verification.",
    )


@router.get(
    "/verify",
    response_model=VerifyResponse,
    responses={400: {"model": ErrorResponse}},
)
def verify_email(
    token: str,
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(_get_settings)],
) -> VerifyResponse:
    """Verify a user's email address using the token from the link."""
    svc = _build_auth_service(session, settings)
    try:
        result = svc.verify_email(token)
    except AppError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error_code": exc.code, "message": exc.message},
        ) from None

    log.info("Email verified via API", extra={"user_id": str(result.user_id)})
    return VerifyResponse(
        user_id=result.user_id,
        email=result.email,
        verified=True,
    )


@router.post(
    "/resend-verification",
    response_model=ResendResponse,
    responses={
        400: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
    },
)
def resend_verification(
    body: ResendRequest,
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(_get_settings)],
) -> ResendResponse:
    """Resend the verification email (rate-limited: 3x/hour)."""
    from src.backend.models.user import User

    user = session.query(User).filter_by(email=body.email).first()
    if user is None:
        return ResendResponse(
            message="If an account exists, a verification email was sent.",
        )

    svc = _build_auth_service(session, settings)
    try:
        svc.resend_verification(user.id)
    except AppError as exc:
        status = _error_status(exc.code)
        raise HTTPException(
            status_code=status,
            detail={"error_code": exc.code, "message": exc.message},
        ) from None

    return ResendResponse(
        message="If an account exists, a verification email was sent.",
    )


def _error_status(code: str) -> int:
    """Map error code to HTTP status."""
    conflict_codes = {"EMAIL_TAKEN", "USERNAME_TAKEN"}
    rate_codes = {"RATE_LIMIT_EXCEEDED"}
    if code in conflict_codes:
        return 409
    if code in rate_codes:
        return 429
    return 400
