"""Request/response schemas for team API endpoints (ADMIN-001)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateTeamRequest(BaseModel):
    """POST /api/v1/teams body."""

    name: str = Field(min_length=1, max_length=200)


class CreateTeamResponse(BaseModel):
    """POST /api/v1/teams response."""

    id: UUID
    owner_id: UUID
    name: str
    created_at: datetime


class TeamMemberResponse(BaseModel):
    """Single member in the members list."""

    id: UUID
    team_id: UUID
    user_id: UUID
    role: str
    invited_at: datetime | None = None
    joined_at: datetime | None = None


class ListMembersResponse(BaseModel):
    """GET /api/v1/teams/{id}/members response."""

    members: list[TeamMemberResponse]


class InviteMemberRequest(BaseModel):
    """POST /api/v1/teams/{id}/invitations body."""

    email: str = Field(max_length=254)
    role: str = Field(default="member", pattern="^(admin|member)$")


class InvitationResponse(BaseModel):
    """POST /api/v1/teams/{id}/invitations response."""

    id: UUID
    team_id: UUID
    email: str
    role: str
    token: str
    created_at: datetime
    expires_at: datetime


class AcceptInvitationResponse(BaseModel):
    """POST /api/v1/invitations/{token}/accept response."""

    team_id: UUID
    user_id: UUID
    role: str


class ChangeRoleRequest(BaseModel):
    """PUT /api/v1/teams/{id}/members/{user_id} body."""

    role: str = Field(pattern="^(admin|member)$")


class ErrorResponse(BaseModel):
    """Standard error response body."""

    error_code: str
    message: str
