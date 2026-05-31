"""Filter rule CRUD API routes (FEAT-002).

All endpoints under /api/v1/filters.
HTTP layer only — business logic lives in advanced_filter_service.py.
"""

import logging
import uuid as _uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.backend.api.filter_schemas import (
    CreateFilterRuleRequest,
    ErrorResponse,
    FilterRuleListResponse,
    FilterRuleResponse,
    TestFilterRequest,
    TestFilterResponse,
    UpdateFilterRuleRequest,
)
from src.backend.db.session import get_session
from src.backend.errors import AppError
from src.backend.models.filter_rule import FilterRule
from src.backend.models.opportunity import Opportunity
from src.backend.services.advanced_filter_service import (
    check_rule_limit,
    test_rule_against_opportunities,
    validate_regex_patterns,
)

log = logging.getLogger("buzzreach.api.filters")

router = APIRouter(prefix="/api/v1", tags=["filters"])

SessionDep = Annotated[Session, Depends(get_session)]


def _stub_current_user_id() -> _uuid.UUID:
    """Stub: placeholder user ID until AUTH-002 is built."""
    return _uuid.UUID("00000000-0000-0000-0000-000000000001")


def _stub_current_plan() -> str:
    """Stub: placeholder plan ID until BILL-002 integration."""
    return "free"


def _handle_app_error(err: AppError) -> HTTPException:
    """Convert an AppError to an HTTPException."""
    status_map: dict[str, int] = {
        "RULE_NOT_FOUND": 404,
        "RULE_LIMIT_REACHED": 402,
        "INVALID_REGEX": 422,
    }
    status = status_map.get(err.code, 400)
    return HTTPException(
        status_code=status,
        detail=ErrorResponse(
            error_code=err.code, message=err.message
        ).model_dump(),
    )


@router.get("/filters", response_model=FilterRuleListResponse)
def api_list_filters(session: SessionDep) -> FilterRuleListResponse:
    """List all filter rules for the current user."""
    user_id = _stub_current_user_id()
    rules = (
        session.query(FilterRule)
        .filter_by(user_id=user_id)
        .order_by(FilterRule.created_at)
        .all()
    )
    return FilterRuleListResponse(
        rules=[FilterRuleResponse.model_validate(r) for r in rules],
        count=len(rules),
    )


@router.post(
    "/filters",
    response_model=FilterRuleResponse,
    status_code=201,
)
def api_create_filter(
    body: CreateFilterRuleRequest,
    session: SessionDep,
) -> FilterRuleResponse:
    """Create a new filter rule."""
    user_id = _stub_current_user_id()
    plan_id = _stub_current_plan()

    try:
        check_rule_limit(session, user_id, plan_id)
    except AppError as err:
        raise _handle_app_error(err) from err

    if body.rule_type == "regex":
        regex_patterns = body.patterns.get("regex", [])
        errors = validate_regex_patterns(regex_patterns)
        if errors:
            raise _handle_app_error(
                AppError(code="INVALID_REGEX", message="; ".join(errors))
            )

    rule = FilterRule(
        user_id=user_id,
        name=body.name,
        rule_type=body.rule_type,
        patterns=body.patterns,
        description=body.description,
        enabled=body.enabled,
    )
    session.add(rule)
    session.commit()

    log.info(
        "Filter rule created",
        extra={"rule_id": str(rule.id), "user_id": str(user_id)},
    )
    return FilterRuleResponse.model_validate(rule)


@router.put("/filters/{rule_id}", response_model=FilterRuleResponse)
def api_update_filter(
    rule_id: _uuid.UUID,
    body: UpdateFilterRuleRequest,
    session: SessionDep,
) -> FilterRuleResponse:
    """Update an existing filter rule."""
    user_id = _stub_current_user_id()
    rule = _get_user_rule(session, rule_id, user_id)

    _apply_rule_updates(rule, body)
    rule.updated_at = datetime.now(UTC)
    session.commit()

    log.info(
        "Filter rule updated",
        extra={"rule_id": str(rule.id), "user_id": str(user_id)},
    )
    return FilterRuleResponse.model_validate(rule)


@router.delete("/filters/{rule_id}", status_code=204)
def api_delete_filter(
    rule_id: _uuid.UUID,
    session: SessionDep,
) -> None:
    """Delete a filter rule."""
    user_id = _stub_current_user_id()
    rule = _get_user_rule(session, rule_id, user_id)
    session.delete(rule)
    session.commit()

    log.info(
        "Filter rule deleted",
        extra={"rule_id": str(rule_id), "user_id": str(user_id)},
    )


@router.post("/filters/{rule_id}/test", response_model=TestFilterResponse)
def api_test_filter(
    rule_id: _uuid.UUID,
    body: TestFilterRequest,
    session: SessionDep,
) -> TestFilterResponse:
    """Test a filter rule against recent opportunities."""
    user_id = _stub_current_user_id()
    rule = _get_user_rule(session, rule_id, user_id)

    opportunities = (
        session.query(Opportunity)
        .order_by(Opportunity.created_at.desc())
        .limit(body.limit)
        .all()
    )

    result = test_rule_against_opportunities(
        opportunities, rule.rule_type, rule.patterns
    )
    return TestFilterResponse(
        rule_id=rule.id,
        total=result.total,
        matched=result.matched,
        rejected=result.rejected,
        sample_rejected=result.sample_rejected,
    )


def _get_user_rule(
    session: Session,
    rule_id: _uuid.UUID,
    user_id: _uuid.UUID,
) -> FilterRule:
    """Load a filter rule owned by the user or raise 404."""
    rule = (
        session.query(FilterRule)
        .filter_by(id=rule_id, user_id=user_id)
        .first()
    )
    if rule is None:
        raise _handle_app_error(
            AppError(code="RULE_NOT_FOUND", message="Filter rule not found")
        )
    return rule


def _apply_rule_updates(
    rule: FilterRule,
    body: UpdateFilterRuleRequest,
) -> None:
    """Apply non-None fields from update request to the rule."""
    if body.name is not None:
        rule.name = body.name
    if body.rule_type is not None:
        rule.rule_type = body.rule_type
    if body.patterns is not None:
        if body.rule_type == "regex" or rule.rule_type == "regex":
            regex_patterns = body.patterns.get("regex", [])
            errors = validate_regex_patterns(regex_patterns)
            if errors:
                raise _handle_app_error(
                    AppError(
                        code="INVALID_REGEX", message="; ".join(errors)
                    )
                )
        rule.patterns = body.patterns
    if body.description is not None:
        rule.description = body.description
    if body.enabled is not None:
        rule.enabled = body.enabled
