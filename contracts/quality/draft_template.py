"""Cross-module contract for draft templates (QUALITY-003).

Defines the public shape of template data consumed by:
- Draft editor (FEAT-001) for template selection
- Template API routes for CRUD operations
- Mobile frontend for template browsing

Cross-module contracts:
- Used by draft editor (FEAT-001)
- Stored per user (AUTH-001)
"""

import enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TemplateCategory(enum.StrEnum):
    """Template categories by platform or style."""

    REDDIT = "reddit"
    QUORA = "quora"
    BLOG = "blog"
    TECHNICAL = "technical"
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    EMPATHETIC = "empathetic"
    PERSUASIVE = "persuasive"


class TemplateCreateRequest(BaseModel):
    """Request body for creating a custom template."""

    name: str = Field(min_length=1, max_length=200)
    category: TemplateCategory
    description: str = Field(min_length=1, max_length=500)
    text: str = Field(min_length=1, max_length=10000)


class TemplateUpdateRequest(BaseModel):
    """Request body for updating a template."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    category: TemplateCategory | None = None
    description: str | None = Field(
        default=None, min_length=1, max_length=500
    )
    text: str | None = Field(default=None, min_length=1, max_length=10000)


class TemplateResponse(BaseModel):
    """Public template representation returned by API endpoints."""

    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID | None = None
    name: str
    category: str
    description: str
    text: str
    is_global: bool
    created_at: datetime
    updated_at: datetime


class TemplateListResponse(BaseModel):
    """Paginated list of templates."""

    items: list[TemplateResponse]
    total: int
