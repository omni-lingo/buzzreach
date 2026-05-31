"""Request/response schemas for bulk opportunity endpoints (FEAT-006)."""

from uuid import UUID

from pydantic import BaseModel, Field


class BulkIdsRequest(BaseModel):
    """Request body for bulk operations — list of opportunity IDs."""

    opportunity_ids: list[UUID] = Field(
        min_length=1,
        max_length=100,
        description="IDs of opportunities to act on",
    )


class BulkResultResponse(BaseModel):
    """Response for bulk archive/regenerate/delete."""

    processed: int
    failed: int
    action: str


class BulkErrorResponse(BaseModel):
    """Standard error response for bulk endpoints."""

    error_code: str
    message: str
