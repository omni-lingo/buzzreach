"""Cross-module contract for search profile data (FEAT-004).

Consumed by:
- FEAT-004 (search scheduler service, search API)
- JOB-001 (scan job reads active profiles)
- DISC-003 (discovery service runs profile searches)
- FE-001 (SearchProfilesPage displays profiles)
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SearchProfileData(BaseModel):
    """Public representation of a search profile for cross-module use."""

    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    name: str
    keywords: list[str]
    platforms: list[str]
    languages: list[str]
    enabled: bool
    created_at: datetime
    updated_at: datetime


class ScheduleConfig(BaseModel):
    """Schedule configuration for a search profile."""

    profile_id: UUID
    times: list[str] = Field(
        description="List of HH:MM times in 24h format, e.g. ['06:00', '14:00']",
    )
    frequency: str = Field(
        default="daily",
        pattern="^(hourly|daily|weekly)$",
        description="How often to run: hourly, daily, or weekly",
    )


class ScheduledSearchInfo(BaseModel):
    """Info about a scheduled search for API responses."""

    model_config = {"from_attributes": True}

    profile_id: UUID
    profile_name: str
    times: list[str]
    frequency: str
    enabled: bool
    next_run: str | None = None


SEARCH_PROFILE_LIMITS: dict[str, int] = {
    "free": 1,
    "pro": 5,
    "premium": 100,
}
