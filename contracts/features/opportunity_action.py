"""Cross-module contract for opportunity action data (FEAT-003).

Consumed by:
- FEAT-003 (action tracker service, opportunities API)
- FE-002 (OpportunityCard action status)
- MOBILE-003 (mobile action logging)
- CORE-005 (metrics expansion — posting_rate, etc.)
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class ActionType(StrEnum):
    """Allowed action types for opportunity tracking."""

    VIEWED = "viewed"
    COPIED = "copied"
    POSTED = "posted"
    ARCHIVED = "archived"


class OpportunityActionData(BaseModel):
    """Public representation of an opportunity action for cross-module use."""

    model_config = {"from_attributes": True}

    id: UUID
    opportunity_id: UUID
    user_id: UUID
    action_type: str
    posted_url: str | None = None
    created_at: datetime


class FunnelCounts(BaseModel):
    """Conversion funnel counts for analytics."""

    discovered: int = Field(
        default=0, description="Total opportunities in system"
    )
    viewed: int = Field(
        default=0, description="Unique opportunities viewed"
    )
    copied: int = Field(
        default=0, description="Unique opportunities with draft copied"
    )
    posted: int = Field(
        default=0, description="Unique opportunities posted"
    )
    archived: int = Field(
        default=0, description="Unique opportunities archived"
    )
    conversion_rate: float = Field(
        default=0.0, description="posted / viewed (0 if no views)"
    )
