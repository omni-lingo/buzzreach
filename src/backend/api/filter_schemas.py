"""Request/response schemas for filter API endpoints (FEAT-002)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CreateFilterRuleRequest(BaseModel):
    """POST /api/v1/filters body."""

    name: str = Field(min_length=1, max_length=200)
    rule_type: str = Field(pattern="^(regex|not|field|composite)$")
    patterns: dict[str, Any]
    description: str = Field(default="", max_length=1000)
    enabled: bool = True


class UpdateFilterRuleRequest(BaseModel):
    """PUT /api/v1/filters/{id} body."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    rule_type: str | None = Field(
        default=None, pattern="^(regex|not|field|composite)$"
    )
    patterns: dict[str, Any] | None = None
    description: str | None = Field(default=None, max_length=1000)
    enabled: bool | None = None


class FilterRuleResponse(BaseModel):
    """Single filter rule in API responses."""

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


class FilterRuleListResponse(BaseModel):
    """GET /api/v1/filters response."""

    rules: list[FilterRuleResponse]
    count: int


class TestFilterRequest(BaseModel):
    """POST /api/v1/filters/{id}/test body."""

    limit: int = Field(default=100, ge=1, le=1000)


class TestFilterResponse(BaseModel):
    """POST /api/v1/filters/{id}/test response."""

    rule_id: UUID
    total: int
    matched: int
    rejected: int
    sample_rejected: list[dict[str, str]] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Standard error response body."""

    error_code: str
    message: str
