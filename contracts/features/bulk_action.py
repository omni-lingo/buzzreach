"""Cross-module contract for bulk action data (FEAT-006).

Consumed by:
- FEAT-006 (bulk action endpoints, BulkActionsBar component)
- FE-002 (opportunity feed integration)
"""

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class BulkActionType(StrEnum):
    """Allowed bulk action types."""

    ARCHIVE = "archive"
    REGENERATE = "regenerate"
    EXPORT = "export"
    DELETE = "delete"


class BulkActionRequest(BaseModel):
    """Request body for bulk operations on opportunities."""

    opportunity_ids: list[UUID] = Field(
        min_length=1,
        max_length=100,
        description="IDs of opportunities to act on",
    )


class BulkActionResult(BaseModel):
    """Result of a bulk operation."""

    processed: int = Field(description="Number successfully processed")
    failed: int = Field(default=0, description="Number that failed")
    action: str = Field(description="The bulk action performed")
