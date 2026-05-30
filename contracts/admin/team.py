"""Cross-module contracts for Team data (ADMIN-001).

These DTOs are the boundary contracts between the admin module and
consumers (API routes, dashboard, opportunity scoping).
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TeamData(BaseModel):
    """Public team representation for cross-module use."""

    model_config = {"from_attributes": True}

    id: UUID
    owner_id: UUID
    name: str
    created_at: datetime


class TeamMemberData(BaseModel):
    """Team membership representation for cross-module use."""

    model_config = {"from_attributes": True}

    id: UUID
    team_id: UUID
    user_id: UUID
    role: str
    invited_at: datetime | None = None
    joined_at: datetime | None = None
    created_at: datetime


class TeamInvitationData(BaseModel):
    """Team invitation representation (excludes token for safety)."""

    model_config = {"from_attributes": True}

    id: UUID
    team_id: UUID
    email: str
    role: str
    is_used: bool = False
    created_at: datetime
    expires_at: datetime


class PlanLimits(BaseModel):
    """Member limits per subscription plan."""

    plan: str = Field(description="Plan name: free, pro, or premium")
    max_members: int = Field(description="Maximum team members allowed")


PLAN_MEMBER_LIMITS: dict[str, int] = {
    "free": 1,
    "pro": 3,
    "premium": 999_999,
}
