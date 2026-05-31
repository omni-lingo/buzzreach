"""Cross-module contract for draft editing (FEAT-001).

Consumed by:
- FEAT-001 (draft editor frontend, save/regenerate API)
- API-001 (draft update endpoints)
- AUDIT-002 (edit history tracking)
"""

from enum import StrEnum

from pydantic import BaseModel, Field


class DraftTone(StrEnum):
    """Predefined tone options for draft regeneration."""

    PROFESSIONAL = "professional"
    CASUAL = "casual"
    HUMOROUS = "humorous"
    TECHNICAL = "technical"
    EMPATHETIC = "empathetic"
    ENTHUSIASTIC = "enthusiastic"


class DraftEditRequest(BaseModel):
    """Request body for saving an edited draft."""

    edited_text: str = Field(min_length=1, max_length=10000)


class DraftRegenerateRequest(BaseModel):
    """Request body for regenerating a draft with a new tone."""

    tone: DraftTone


class DraftResponse(BaseModel):
    """Response containing current and original draft text."""

    model_config = {"from_attributes": True}

    original_draft: str
    edited_draft: str | None = None
    current_text: str = Field(
        description="The active draft text (edited if present, else original)"
    )
