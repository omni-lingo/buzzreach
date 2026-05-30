"""Team management service (ADMIN-001).

Pure business logic — no HTTP concerns. All functions take a SQLAlchemy
session and operate on Team, TeamMember, and TeamInvitation models.
"""

import logging
import uuid as _uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from src.backend.models.team import Team
from src.backend.models.team_invitation import TeamInvitation
from src.backend.models.team_member import TeamMember, TeamRole
from src.backend.services.team_errors import (
    AlreadyMemberError,
    CannotRemoveOwnerError,
    InvitationExpiredError,
    InvitationNotFoundError,
    InvitationUsedError,
    MemberNotFoundError,
    PermissionDeniedError,
)
from src.backend.services.team_helpers import (
    check_permission,
    check_plan_limit,
    get_member_role,
)

log = logging.getLogger("buzzreach")


def create_team(
    session: Session,
    owner_id: _uuid.UUID,
    name: str,
) -> Team:
    """Create a new team and add the owner as a member."""
    team = Team(owner_id=owner_id, name=name)
    session.add(team)
    session.flush()

    member = TeamMember(
        team_id=team.id,
        user_id=owner_id,
        role=TeamRole.OWNER,
        joined_at=datetime.now(UTC),
    )
    session.add(member)
    session.commit()

    log.info(
        "Team created",
        extra={"team_id": str(team.id), "owner_id": str(owner_id)},
    )
    return team


def list_team_members(
    session: Session,
    team_id: _uuid.UUID,
) -> list[TeamMember]:
    """Return all members of a team."""
    return (
        session.query(TeamMember)
        .filter(TeamMember.team_id == team_id)
        .all()
    )


def invite_member(
    session: Session,
    team_id: _uuid.UUID,
    email: str,
    role: str,
    actor_id: _uuid.UUID,
) -> TeamInvitation:
    """Create an invitation for an email to join the team."""
    check_permission(session, team_id, actor_id, "invite_member")
    check_plan_limit(session, team_id)

    invitation = TeamInvitation(
        team_id=team_id,
        email=email,
        role=role,
    )
    session.add(invitation)
    session.commit()

    log.info(
        "Invitation created",
        extra={
            "team_id": str(team_id),
            "email": email,
            "role": role,
        },
    )
    return invitation


def accept_invitation(
    session: Session,
    token: str,
    user_id: _uuid.UUID,
) -> TeamMember:
    """Accept a pending invitation and join the team."""
    invitation = (
        session.query(TeamInvitation)
        .filter(TeamInvitation.token == token)
        .first()
    )
    if invitation is None:
        raise InvitationNotFoundError

    if invitation.is_used:
        raise InvitationUsedError

    now = datetime.now(UTC)
    if now > invitation.expires_at.replace(tzinfo=UTC):
        raise InvitationExpiredError

    existing = get_member_role(session, invitation.team_id, user_id)
    if existing is not None:
        raise AlreadyMemberError

    check_plan_limit(session, invitation.team_id)

    role = TeamRole(invitation.role)
    member = TeamMember(
        team_id=invitation.team_id,
        user_id=user_id,
        role=role,
        invited_at=invitation.created_at,
        joined_at=now,
    )
    session.add(member)

    invitation.is_used = True
    session.commit()

    log.info(
        "Invitation accepted",
        extra={
            "team_id": str(invitation.team_id),
            "user_id": str(user_id),
        },
    )
    return member


def change_member_role(
    session: Session,
    team_id: _uuid.UUID,
    user_id: _uuid.UUID,
    new_role: str,
    actor_id: _uuid.UUID,
) -> TeamMember:
    """Change a team member's role. Only owner/admin can do this."""
    actor = check_permission(
        session, team_id, actor_id, "change_member_role"
    )

    target = get_member_role(session, team_id, user_id)
    if target is None:
        raise MemberNotFoundError

    if target.role == TeamRole.OWNER:
        raise PermissionDeniedError("cannot change owner role")

    if (
        actor.role == TeamRole.ADMIN
        and TeamRole(new_role) == TeamRole.OWNER
    ):
        raise PermissionDeniedError("admin cannot promote to owner")

    target.role = TeamRole(new_role)
    session.commit()

    log.info(
        "Member role changed",
        extra={
            "team_id": str(team_id),
            "user_id": str(user_id),
            "new_role": new_role,
        },
    )
    return target


def remove_member(
    session: Session,
    team_id: _uuid.UUID,
    user_id: _uuid.UUID,
    actor_id: _uuid.UUID,
) -> None:
    """Remove a member from the team. Only owner/admin can do this."""
    check_permission(session, team_id, actor_id, "remove_member")

    target = get_member_role(session, team_id, user_id)
    if target is None:
        raise MemberNotFoundError

    if target.role == TeamRole.OWNER:
        raise CannotRemoveOwnerError

    session.delete(target)
    session.commit()

    log.info(
        "Member removed",
        extra={
            "team_id": str(team_id),
            "user_id": str(user_id),
        },
    )
