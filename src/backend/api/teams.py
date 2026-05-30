"""Team management API routes (ADMIN-001).

All endpoints under /api/v1/teams and /api/v1/invitations.
HTTP layer only — business logic lives in team_service.py.
"""

import uuid as _uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.backend.api.team_schemas import (
    AcceptInvitationResponse,
    ChangeRoleRequest,
    CreateTeamRequest,
    CreateTeamResponse,
    ErrorResponse,
    InvitationResponse,
    InviteMemberRequest,
    ListMembersResponse,
    TeamMemberResponse,
)
from src.backend.db.session import get_session
from src.backend.services.team_errors import TeamError
from src.backend.services.team_service import (
    accept_invitation,
    change_member_role,
    create_team,
    invite_member,
    list_team_members,
    remove_member,
)

router = APIRouter(prefix="/api/v1", tags=["teams"])

SessionDep = Annotated[Session, Depends(get_session)]

_ERROR_STATUS: dict[str, int] = {
    "TEAM_NOT_FOUND": 404,
    "MEMBER_NOT_FOUND": 404,
    "INVITATION_NOT_FOUND": 404,
    "INVITATION_EXPIRED": 410,
    "INVITATION_ALREADY_USED": 409,
    "PERMISSION_DENIED": 403,
    "PLAN_LIMIT_REACHED": 402,
    "ALREADY_MEMBER": 409,
    "CANNOT_REMOVE_OWNER": 403,
}


def _handle_team_error(err: TeamError) -> HTTPException:
    """Convert a TeamError to an HTTPException with error code."""
    status = _ERROR_STATUS.get(err.code, 400)
    return HTTPException(
        status_code=status,
        detail=ErrorResponse(
            error_code=err.code, message=err.message
        ).model_dump(),
    )


def _stub_current_user_id() -> _uuid.UUID:
    """Stub: return a placeholder user ID until AUTH-002 is built."""
    return _uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.post(
    "/teams",
    response_model=CreateTeamResponse,
    status_code=201,
)
def api_create_team(
    body: CreateTeamRequest,
    session: SessionDep,
) -> CreateTeamResponse:
    """Create a new team workspace."""
    user_id = _stub_current_user_id()
    try:
        team = create_team(session, user_id, body.name)
    except TeamError as err:
        raise _handle_team_error(err) from err
    return CreateTeamResponse(
        id=team.id,
        owner_id=team.owner_id,
        name=team.name,
        created_at=team.created_at,
    )


@router.get(
    "/teams/{team_id}/members",
    response_model=ListMembersResponse,
)
def api_list_members(
    team_id: _uuid.UUID,
    session: SessionDep,
) -> ListMembersResponse:
    """List all members of a team."""
    try:
        members = list_team_members(session, team_id)
    except TeamError as err:
        raise _handle_team_error(err) from err
    return ListMembersResponse(
        members=[
            TeamMemberResponse(
                id=m.id,
                team_id=m.team_id,
                user_id=m.user_id,
                role=m.role.value if hasattr(m.role, "value") else m.role,
                invited_at=m.invited_at,
                joined_at=m.joined_at,
            )
            for m in members
        ]
    )


@router.post(
    "/teams/{team_id}/invitations",
    response_model=InvitationResponse,
    status_code=201,
)
def api_invite_member(
    team_id: _uuid.UUID,
    body: InviteMemberRequest,
    session: SessionDep,
) -> InvitationResponse:
    """Send an invitation to join the team."""
    user_id = _stub_current_user_id()
    try:
        inv = invite_member(
            session, team_id, body.email, body.role, user_id
        )
    except TeamError as err:
        raise _handle_team_error(err) from err
    return InvitationResponse(
        id=inv.id,
        team_id=inv.team_id,
        email=inv.email,
        role=inv.role,
        token=inv.token,
        created_at=inv.created_at,
        expires_at=inv.expires_at,
    )


@router.post(
    "/invitations/{token}/accept",
    response_model=AcceptInvitationResponse,
)
def api_accept_invitation(
    token: str,
    session: SessionDep,
) -> AcceptInvitationResponse:
    """Accept a team invitation using the one-time token."""
    user_id = _stub_current_user_id()
    try:
        member = accept_invitation(session, token, user_id)
    except TeamError as err:
        raise _handle_team_error(err) from err
    role_val = (
        member.role.value if hasattr(member.role, "value") else member.role
    )
    return AcceptInvitationResponse(
        team_id=member.team_id,
        user_id=member.user_id,
        role=role_val,
    )


@router.put(
    "/teams/{team_id}/members/{user_id}",
    response_model=TeamMemberResponse,
)
def api_change_role(
    team_id: _uuid.UUID,
    user_id: _uuid.UUID,
    body: ChangeRoleRequest,
    session: SessionDep,
) -> TeamMemberResponse:
    """Change a team member's role."""
    actor_id = _stub_current_user_id()
    try:
        member = change_member_role(
            session, team_id, user_id, body.role, actor_id
        )
    except TeamError as err:
        raise _handle_team_error(err) from err
    role_val = (
        member.role.value if hasattr(member.role, "value") else member.role
    )
    return TeamMemberResponse(
        id=member.id,
        team_id=member.team_id,
        user_id=member.user_id,
        role=role_val,
        invited_at=member.invited_at,
        joined_at=member.joined_at,
    )


@router.delete(
    "/teams/{team_id}/members/{user_id}",
    status_code=204,
)
def api_remove_member(
    team_id: _uuid.UUID,
    user_id: _uuid.UUID,
    session: SessionDep,
) -> None:
    """Remove a member from the team."""
    actor_id = _stub_current_user_id()
    try:
        remove_member(session, team_id, user_id, actor_id)
    except TeamError as err:
        raise _handle_team_error(err) from err
