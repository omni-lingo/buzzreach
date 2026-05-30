"""Cross-module contract for per-product configuration (CFG-001).

This DTO is the boundary contract between the config module and all
consumers: DISC-001, FILT-002, AI-002, AI-003, PIPE-001.
"""

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class ProductConfig(BaseModel):
    """Per-product configuration for BuzzReach scanning.

    One JSON file per product (e.g., irs_calculator.json). Loaded by
    CFG-002's config_loader. Strict validation; no extra fields.
    """

    model_config = {"extra": "forbid"}

    slug: str = Field(min_length=1)
    product_url: HttpUrl
    pitch: str = Field(min_length=1)
    niche: str = Field(min_length=1)
    keywords: list[str] = Field(min_length=1)
    tone: str = Field(min_length=1)
    mention: str = Field(min_length=1)
    freshness: Literal["h", "d", "w"] = "d"
    max_queries: int = Field(default=5, ge=1)
