"""Internal helpers for team service (ADMIN-001).

Shared query/validation functions used by team_service.py.
Not part of the public API — only imported by team_service.
"""

import uuid as _uuid

from sqlalchemy.orm import Session

from contracts.admin.team import PLAN_MEMBER_LIMITS
from src.backend.models.team import Team
from src.backend.models.team_member import TeamMember, TeamRole
from src.backend.services.team_errors import (
    PermissionDeniedError,
    PlanLimitError,
    TeamNotFoundError,
)


def get_team(session: Session, team_id: _uuid.UUID) -> Team:
    """Fetch a team by ID or raise TeamNotFoundError."""
    team = session.get(Team, team_id)
    if team is None:
        raise TeamNotFoundError(str(team_id))
    return team


def get_member_role(
    session: Session,
    team_id: _uuid.UUID,
    user_id: _uuid.UUID,
) -> TeamMember | None:
    """Fetch a specific membership record."""
    return (
        session.query(TeamMember)
        .filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
        )
        .first()
    )


def check_permission(
    session: Session,
    team_id: _uuid.UUID,
    actor_id: _uuid.UUID,
    action: str,
) -> TeamMember:
    """Verify actor is owner or admin; raise PermissionDeniedError."""
    member = get_member_role(session, team_id, actor_id)
    if member is None:
        raise PermissionDeniedError(action)
    if member.role not in (TeamRole.OWNER, TeamRole.ADMIN):
        raise PermissionDeniedError(action)
    return member


def count_members(session: Session, team_id: _uuid.UUID) -> int:
    """Count current members in a team."""
    return (
        session.query(TeamMember)
        .filter(TeamMember.team_id == team_id)
        .count()
    )


def get_team_plan(team_id: _uuid.UUID) -> str:
    """Get the plan for a team. Stub until BILL-002 is built."""
    _ = team_id
    return "free"


def check_plan_limit(
    session: Session,
    team_id: _uuid.UUID,
) -> None:
    """Raise PlanLimitError if the team has reached its member limit."""
    plan = get_team_plan(team_id)
    limit = PLAN_MEMBER_LIMITS.get(plan, 1)
    current = count_members(session, team_id)
    if current >= limit:
        raise PlanLimitError(limit)
