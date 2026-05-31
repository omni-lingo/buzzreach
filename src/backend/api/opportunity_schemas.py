"""Request/response schemas for opportunity action API endpoints (FEAT-003)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LogActionRequest(BaseModel):
    """POST /api/v1/opportunities/{id}/actions body."""

    action_type: str = Field(
        pattern="^(viewed|copied|posted|archived)$"
    )
    posted_url: str | None = Field(
        default=None, max_length=2048
    )


class ActionResponse(BaseModel):
    """Single action in API responses."""

    model_config = {"from_attributes": True}

    id: UUID
    opportunity_id: UUID
    user_id: UUID
    action_type: str
    posted_url: str | None = None
    created_at: datetime


class ActionListResponse(BaseModel):
    """GET /api/v1/opportunities/{id}/actions response."""

    actions: list[ActionResponse]
    count: int


class FunnelResponse(BaseModel):
    """GET /api/v1/analytics/funnel response."""

    discovered: int = 0
    viewed: int = 0
    copied: int = 0
    posted: int = 0
    archived: int = 0
    conversion_rate: float = 0.0


class DeleteActionsResponse(BaseModel):
    """DELETE /api/v1/actions/me response."""

    deleted_count: int


class ErrorResponse(BaseModel):
    """Standard error response body."""

    error_code: str
    message: str
