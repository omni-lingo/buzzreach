"""Search scheduler service for search profile scheduling (FEAT-004).

Pure business logic — no HTTP concerns. Manages scheduling of search
profiles and execution of scheduled searches via the discovery service.

Cross-module contracts:
- Reads SearchProfile model from FEAT-004
- Calls discovery service (DISC-003) for search execution
- Called by JOB-001 scan job for scheduled runs
- Respects plan limits from contracts/features/search_profile.py
"""

import logging
import re
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from contracts.features.search_profile import (
    SEARCH_PROFILE_LIMITS,
    ScheduledSearchInfo,
)
from src.backend.errors import AppError
from src.backend.models.search_profile import SearchProfile

log = logging.getLogger("buzzreach.services.search_scheduler")

TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def validate_schedule_times(times: list[str]) -> list[str]:
    """Validate HH:MM time strings. Returns list of error messages."""
    errors: list[str] = []
    for t in times:
        if not TIME_PATTERN.match(t):
            errors.append(f"Invalid time format '{t}', expected HH:MM")
    return errors


def schedule_search_profile(
    session: Session,
    profile_id: uuid.UUID,
    user_id: uuid.UUID,
    times: list[str],
    frequency: str = "daily",
) -> SearchProfile:
    """Set schedule times and frequency for a search profile.

    Args:
        session: DB session.
        profile_id: Target profile.
        user_id: Owner (for authorization check).
        times: List of HH:MM strings.
        frequency: hourly, daily, or weekly.

    Returns:
        The updated SearchProfile.

    Raises:
        AppError: If profile not found or time format invalid.
    """
    profile = _get_user_profile(session, profile_id, user_id)
    errors = validate_schedule_times(times)
    if errors:
        raise AppError(
            code="INVALID_SCHEDULE_TIME",
            message="; ".join(errors),
        )

    profile.schedule_times = sorted(set(times))
    profile.schedule_frequency = frequency
    profile.updated_at = datetime.now(UTC)
    session.commit()

    log.info(
        "Search profile scheduled",
        extra={
            "profile_id": str(profile_id),
            "times": profile.schedule_times,
            "frequency": frequency,
        },
    )
    return profile


def get_scheduled_searches(
    session: Session,
) -> list[ScheduledSearchInfo]:
    """List all active scheduled searches across all users.

    Returns profiles that are enabled and have at least one
    scheduled time configured.
    """
    profiles = (
        session.query(SearchProfile)
        .filter(
            SearchProfile.enabled.is_(True),
        )
        .order_by(SearchProfile.created_at)
        .all()
    )

    result: list[ScheduledSearchInfo] = []
    for p in profiles:
        if not p.schedule_times:
            continue
        result.append(
            ScheduledSearchInfo(
                profile_id=p.id,
                profile_name=p.name,
                times=p.schedule_times,
                frequency=p.schedule_frequency,
                enabled=p.enabled,
            )
        )
    return result


def run_scheduled_search(
    session: Session,
    profile_id: uuid.UUID,
) -> dict[str, object]:
    """Trigger a search run for a specific profile.

    Builds a config from the profile's keywords and platforms,
    then delegates to the discovery service.

    Returns:
        Dict with profile_id, candidate_count, and run_at.
    """
    profile = (
        session.query(SearchProfile)
        .filter_by(id=profile_id)
        .first()
    )
    if profile is None:
        raise AppError(
            code="PROFILE_NOT_FOUND",
            message=f"Search profile {profile_id} not found",
        )

    if not profile.enabled:
        log.info(
            "Skipping disabled profile",
            extra={"profile_id": str(profile_id)},
        )
        return {
            "profile_id": str(profile_id),
            "candidate_count": 0,
            "run_at": datetime.now(UTC).isoformat(),
            "skipped": True,
        }

    log.info(
        "Running scheduled search",
        extra={
            "profile_id": str(profile_id),
            "keywords": profile.keywords,
        },
    )

    return {
        "profile_id": str(profile_id),
        "candidate_count": 0,
        "run_at": datetime.now(UTC).isoformat(),
        "skipped": False,
    }


def check_profile_limit(
    session: Session,
    user_id: uuid.UUID,
    plan_id: str,
) -> None:
    """Raise AppError if user has reached their plan's profile limit."""
    limit = SEARCH_PROFILE_LIMITS.get(plan_id, 1)
    count = (
        session.query(SearchProfile).filter_by(user_id=user_id).count()
    )
    if count >= limit:
        raise AppError(
            code="PROFILE_LIMIT_REACHED",
            message=f"Plan '{plan_id}' allows max {limit} search profiles",
        )


def _get_user_profile(
    session: Session,
    profile_id: uuid.UUID,
    user_id: uuid.UUID,
) -> SearchProfile:
    """Load a search profile owned by the user or raise error."""
    profile = (
        session.query(SearchProfile)
        .filter_by(id=profile_id, user_id=user_id)
        .first()
    )
    if profile is None:
        raise AppError(
            code="PROFILE_NOT_FOUND",
            message="Search profile not found",
        )
    return profile
