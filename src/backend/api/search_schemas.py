"""Request/response schemas for search profile API endpoints (FEAT-004)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateSearchProfileRequest(BaseModel):
    """POST /api/v1/search-profiles body."""

    name: str = Field(min_length=1, max_length=200)
    keywords: list[str] = Field(min_length=1)
    platforms: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    enabled: bool = True
    copy_from: UUID | None = Field(
        default=None,
        description="Profile ID to copy settings from",
    )


class UpdateSearchProfileRequest(BaseModel):
    """PUT /api/v1/search-profiles/{id} body."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    keywords: list[str] | None = None
    platforms: list[str] | None = None
    languages: list[str] | None = None
    enabled: bool | None = None


class SetScheduleRequest(BaseModel):
    """POST /api/v1/search-profiles/{id}/schedule body."""

    times: list[str] = Field(
        min_length=1,
        description="HH:MM times in 24h format",
    )
    frequency: str = Field(
        default="daily",
        pattern="^(hourly|daily|weekly)$",
    )


class SearchProfileResponse(BaseModel):
    """Single search profile in API responses."""

    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    name: str
    keywords: list[str]
    platforms: list[str]
    languages: list[str]
    schedule_times: list[str]
    schedule_frequency: str
    enabled: bool
    created_at: datetime
    updated_at: datetime


class SearchProfileListResponse(BaseModel):
    """GET /api/v1/search-profiles response."""

    profiles: list[SearchProfileResponse]
    count: int


class ScheduleResponse(BaseModel):
    """POST /api/v1/search-profiles/{id}/schedule response."""

    profile_id: UUID
    times: list[str]
    frequency: str


class ErrorResponse(BaseModel):
    """Standard error response body."""

    error_code: str
    message: str
