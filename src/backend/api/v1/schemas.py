"""Request/response schemas for the Opportunities API (API-001).

OpportunityResponse wraps OpportunityData for stable API output.
ErrorResponse provides coded error bodies to clients.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OpportunityResponse(BaseModel):
    """Public opportunity representation returned by all endpoints."""

    model_config = {"from_attributes": True}

    id: UUID
    niche: str
    url: str
    title: str
    source: str
    why_matched: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    draft_reply: str
    edited_draft: str | None = None
    status: str
    created_at: datetime
    delivered_at: datetime | None = None


class ErrorResponse(BaseModel):
    """Standard coded error response body."""

    error_code: str
    message: str
