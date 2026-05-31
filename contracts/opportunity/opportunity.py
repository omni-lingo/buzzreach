"""Cross-module contract for Opportunity data.

This DTO is the boundary contract between the core module (Opportunity model)
and all consumers: PIPE-001 (pipeline writes), DELIV-001 (delivery reads),
and API-001 (API reads). Changing this file breaks those modules at import time.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OpportunityData(BaseModel):
    """Public representation of an opportunity for cross-module use.

    Mirrors the Opportunity ORM row shape. Imported by pipeline,
    delivery, and api modules.
    """

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
    status: str = "new"
    created_at: datetime
    delivered_at: datetime | None = None
