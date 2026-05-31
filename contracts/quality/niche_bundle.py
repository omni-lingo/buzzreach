"""Cross-module contract for niche bundles (QUALITY-004).

Defines the public shape of pre-configured niche profile bundles.

Consumed by:
- NicheBundles page (QUALITY-004 frontend)
- Niche bundle API routes
- Onboarding wizard (ONBOARD-003) for quick-start profiles

Cross-module contracts:
- Extends search profiles (FEAT-004) — bundle creates a SearchProfile
- Uses templates (QUALITY-003) — bundles include draft templates
- Helps onboarding flow (ONBOARD-003)
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BundleTemplate(BaseModel):
    """A draft template included in a niche bundle."""

    name: str
    category: str
    description: str
    text: str


class NicheBundleData(BaseModel):
    """Public representation of a niche bundle for API responses."""

    model_config = {"from_attributes": True}

    id: UUID
    name: str
    slug: str
    description: str
    keywords: list[str]
    platforms: list[str]
    tone: str
    tone_description: str
    templates: list[BundleTemplate]
    icon: str
    created_at: datetime
    updated_at: datetime


class NicheBundleListResponse(BaseModel):
    """List of available niche bundles."""

    items: list[NicheBundleData]
    total: int


class ApplyBundleRequest(BaseModel):
    """Request to apply a niche bundle as a search profile."""

    bundle_id: UUID
    profile_name: str = Field(min_length=1, max_length=200)
    keywords: list[str] | None = Field(
        default=None,
        description="Override bundle keywords (uses bundle defaults if None)",
    )
    platforms: list[str] | None = Field(
        default=None,
        description="Override bundle platforms (uses bundle defaults if None)",
    )


class ApplyBundleResponse(BaseModel):
    """Response after applying a niche bundle."""

    profile_id: UUID
    profile_name: str
    bundle_name: str
    keywords: list[str]
    platforms: list[str]
    message: str
