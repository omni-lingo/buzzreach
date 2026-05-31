"""Push notification API endpoints (MOBILE-002).

POST /api/v1/push/register   — client registers device token
POST /api/v1/push/unregister — client marks token inactive

All endpoints require JWT authentication.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from contracts.auth.user import UserData
from contracts.push.push_subscription import DevicePlatform
from src.backend.api.auth_deps import get_current_user
from src.backend.db.session import get_session
from src.backend.errors import AppError
from src.backend.services.push_service import PushService

log = logging.getLogger("buzzreach.api.push")

router = APIRouter(
    prefix="/api/v1/push",
    tags=["push-notifications"],
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[UserData, Depends(get_current_user)]


class RegisterRequest(BaseModel):
    """Request body for device token registration."""

    device_token: str = Field(
        min_length=1,
        max_length=512,
        description="Expo push token string",
    )
    platform: DevicePlatform = Field(
        description="Device platform (ios or android)",
    )


class UnregisterRequest(BaseModel):
    """Request body for device token unregistration."""

    device_token: str = Field(
        min_length=1,
        max_length=512,
        description="Expo push token to deactivate",
    )


class PushSubscriptionResponse(BaseModel):
    """Response after register/unregister operations."""

    model_config = {"from_attributes": True}

    id: str
    user_id: str
    device_token: str
    platform: str
    is_active: bool


@router.post(
    "/register",
    response_model=PushSubscriptionResponse,
    status_code=201,
)
def register_device(
    request: RegisterRequest,
    session: SessionDep,
    user: CurrentUser,
) -> PushSubscriptionResponse:
    """Register a device push token for the current user."""
    svc = PushService(session)
    sub = svc.register_token(
        user_id=user.id,
        device_token=request.device_token,
        platform=request.platform.value,
    )
    log.info(
        "Device registered",
        extra={
            "user_id": str(user.id),
            "platform": request.platform.value,
        },
    )
    return PushSubscriptionResponse(
        id=str(sub.id),
        user_id=str(sub.user_id),
        device_token=sub.device_token,
        platform=sub.platform,
        is_active=sub.is_active,
    )


@router.post(
    "/unregister",
    response_model=PushSubscriptionResponse,
)
def unregister_device(
    request: UnregisterRequest,
    session: SessionDep,
    user: CurrentUser,
) -> PushSubscriptionResponse:
    """Mark a device push token as inactive."""
    svc = PushService(session)
    try:
        sub = svc.unregister_token(
            user_id=user.id,
            device_token=request.device_token,
        )
    except AppError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": exc.code,
                "message": exc.message,
            },
        ) from None

    log.info(
        "Device unregistered",
        extra={"user_id": str(user.id)},
    )
    return PushSubscriptionResponse(
        id=str(sub.id),
        user_id=str(sub.user_id),
        device_token=sub.device_token,
        platform=sub.platform,
        is_active=sub.is_active,
    )
