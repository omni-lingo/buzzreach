"""Cross-module contract for filter rule data (FEAT-002).

Consumed by:
- FEAT-002 (advanced filter service)
- PIPE-001 (pipeline applies user rules)
- API-001 (filter CRUD endpoints)
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class RuleType(StrEnum):
    """Allowed filter rule types."""

    REGEX = "regex"
    NOT = "not"
    FIELD = "field"
    COMPOSITE = "composite"


class FilterRuleData(BaseModel):
    """Public representation of a filter rule for cross-module use."""

    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    name: str
    rule_type: str
    patterns: dict[str, Any]
    description: str
    enabled: bool
    created_at: datetime
    updated_at: datetime


class FilterTestResult(BaseModel):
    """Result of testing a filter rule against opportunities."""

    rule_id: UUID | None = None
    total: int
    matched: int
    rejected: int
    sample_rejected: list[dict[str, str]] = Field(default_factory=list)


# Plan limits for filter rules per plan tier.
FILTER_RULE_LIMITS: dict[str, int] = {
    "free": 3,
    "pro": 20,
    "premium": 100,
}
