"""Search profile CRUD and scheduling API routes (FEAT-004).

All endpoints under /api/v1/search-profiles.
HTTP layer only — business logic lives in search_scheduler.py.
"""

import logging
import uuid as _uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.backend.api.search_schemas import (
    CreateSearchProfileRequest,
    ErrorResponse,
    ScheduleResponse,
    SearchProfileListResponse,
    SearchProfileResponse,
    SetScheduleRequest,
    UpdateSearchProfileRequest,
)
from src.backend.db.session import get_session
from src.backend.errors import AppError
from src.backend.models.search_profile import SearchProfile
from src.backend.services.search_scheduler import (
    check_profile_limit,
    schedule_search_profile,
)

log = logging.getLogger("buzzreach.api.search")

router = APIRouter(prefix="/api/v1", tags=["search-profiles"])

SessionDep = Annotated[Session, Depends(get_session)]


def _stub_current_user_id() -> _uuid.UUID:
    """Stub: placeholder user ID until AUTH-002 is built."""
    return _uuid.UUID("00000000-0000-0000-0000-000000000001")


def _stub_current_plan() -> str:
    """Stub: placeholder plan ID until BILL-002 integration."""
    return "free"


def _handle_app_error(err: AppError) -> HTTPException:
    """Convert an AppError to an HTTPException."""
    status_map: dict[str, int] = {
        "PROFILE_NOT_FOUND": 404,
        "PROFILE_LIMIT_REACHED": 402,
        "INVALID_SCHEDULE_TIME": 422,
    }
    status = status_map.get(err.code, 400)
    return HTTPException(
        status_code=status,
        detail=ErrorResponse(
            error_code=err.code, message=err.message
        ).model_dump(),
    )


@router.get(
    "/search-profiles",
    response_model=SearchProfileListResponse,
)
def api_list_profiles(
    session: SessionDep,
) -> SearchProfileListResponse:
    """List all search profiles for the current user."""
    user_id = _stub_current_user_id()
    profiles = (
        session.query(SearchProfile)
        .filter_by(user_id=user_id)
        .order_by(SearchProfile.created_at)
        .all()
    )
    return SearchProfileListResponse(
        profiles=[
            SearchProfileResponse.model_validate(p) for p in profiles
        ],
        count=len(profiles),
    )


@router.post(
    "/search-profiles",
    response_model=SearchProfileResponse,
    status_code=201,
)
def api_create_profile(
    body: CreateSearchProfileRequest,
    session: SessionDep,
) -> SearchProfileResponse:
    """Create a new search profile, optionally copying from existing."""
    user_id = _stub_current_user_id()
    plan_id = _stub_current_plan()

    try:
        check_profile_limit(session, user_id, plan_id)
    except AppError as err:
        raise _handle_app_error(err) from err

    if body.copy_from is not None:
        return _create_from_copy(session, user_id, body)

    profile = SearchProfile(
        user_id=user_id,
        name=body.name,
        keywords=body.keywords,
        platforms=body.platforms,
        languages=body.languages,
        enabled=body.enabled,
    )
    session.add(profile)
    session.commit()

    log.info(
        "Search profile created",
        extra={"profile_id": str(profile.id), "user_id": str(user_id)},
    )
    return SearchProfileResponse.model_validate(profile)


def _create_from_copy(
    session: Session,
    user_id: _uuid.UUID,
    body: CreateSearchProfileRequest,
) -> SearchProfileResponse:
    """Create a profile by copying settings from an existing one."""
    source = (
        session.query(SearchProfile)
        .filter_by(id=body.copy_from, user_id=user_id)
        .first()
    )
    if source is None:
        raise _handle_app_error(
            AppError(
                code="PROFILE_NOT_FOUND",
                message="Source profile not found",
            )
        )

    profile = SearchProfile(
        user_id=user_id,
        name=body.name,
        keywords=body.keywords or source.keywords,
        platforms=body.platforms or source.platforms,
        languages=body.languages or source.languages,
        enabled=body.enabled,
        schedule_times=source.schedule_times,
        schedule_frequency=source.schedule_frequency,
    )
    session.add(profile)
    session.commit()

    log.info(
        "Search profile copied",
        extra={
            "profile_id": str(profile.id),
            "copied_from": str(body.copy_from),
        },
    )
    return SearchProfileResponse.model_validate(profile)


@router.put(
    "/search-profiles/{profile_id}",
    response_model=SearchProfileResponse,
)
def api_update_profile(
    profile_id: _uuid.UUID,
    body: UpdateSearchProfileRequest,
    session: SessionDep,
) -> SearchProfileResponse:
    """Update an existing search profile."""
    user_id = _stub_current_user_id()
    profile = _get_user_profile(session, profile_id, user_id)

    _apply_profile_updates(profile, body)
    profile.updated_at = datetime.now(UTC)
    session.commit()

    log.info(
        "Search profile updated",
        extra={
            "profile_id": str(profile.id),
            "user_id": str(user_id),
        },
    )
    return SearchProfileResponse.model_validate(profile)


@router.delete("/search-profiles/{profile_id}", status_code=204)
def api_delete_profile(
    profile_id: _uuid.UUID,
    session: SessionDep,
) -> None:
    """Delete a search profile."""
    user_id = _stub_current_user_id()
    profile = _get_user_profile(session, profile_id, user_id)
    session.delete(profile)
    session.commit()

    log.info(
        "Search profile deleted",
        extra={
            "profile_id": str(profile_id),
            "user_id": str(user_id),
        },
    )


@router.post(
    "/search-profiles/{profile_id}/schedule",
    response_model=ScheduleResponse,
)
def api_set_schedule(
    profile_id: _uuid.UUID,
    body: SetScheduleRequest,
    session: SessionDep,
) -> ScheduleResponse:
    """Set the schedule for a search profile."""
    user_id = _stub_current_user_id()
    try:
        profile = schedule_search_profile(
            session, profile_id, user_id, body.times, body.frequency
        )
    except AppError as err:
        raise _handle_app_error(err) from err

    return ScheduleResponse(
        profile_id=profile.id,
        times=profile.schedule_times,
        frequency=profile.schedule_frequency,
    )


def _get_user_profile(
    session: Session,
    profile_id: _uuid.UUID,
    user_id: _uuid.UUID,
) -> SearchProfile:
    """Load a search profile owned by the user or raise 404."""
    profile = (
        session.query(SearchProfile)
        .filter_by(id=profile_id, user_id=user_id)
        .first()
    )
    if profile is None:
        raise _handle_app_error(
            AppError(
                code="PROFILE_NOT_FOUND",
                message="Search profile not found",
            )
        )
    return profile


def _apply_profile_updates(
    profile: SearchProfile,
    body: UpdateSearchProfileRequest,
) -> None:
    """Apply non-None fields from update request to the profile."""
    if body.name is not None:
        profile.name = body.name
    if body.keywords is not None:
        profile.keywords = body.keywords
    if body.platforms is not None:
        profile.platforms = body.platforms
    if body.languages is not None:
        profile.languages = body.languages
    if body.enabled is not None:
        profile.enabled = body.enabled
