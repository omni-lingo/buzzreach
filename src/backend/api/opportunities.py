"""Opportunity action tracking API routes (FEAT-003).

All endpoints under /api/v1/opportunities/{id}/actions and
/api/v1/analytics/funnel. HTTP layer only — business logic
lives in action_tracker.py.
"""

import logging
import uuid as _uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from contracts.features.opportunity_action import ActionType
from src.backend.api.opportunity_schemas import (
    ActionListResponse,
    ActionResponse,
    DeleteActionsResponse,
    ErrorResponse,
    FunnelResponse,
    LogActionRequest,
)
from src.backend.db.session import get_session
from src.backend.errors import AppError
from src.backend.services.action_tracker import (
    delete_user_actions,
    get_action_history,
    get_funnel_counts,
    log_action,
)

log = logging.getLogger("buzzreach.api.opportunities")

router = APIRouter(prefix="/api/v1", tags=["opportunities"])

SessionDep = Annotated[Session, Depends(get_session)]


def _stub_current_user_id() -> _uuid.UUID:
    """Stub: placeholder user ID until AUTH-002 is built."""
    return _uuid.UUID("00000000-0000-0000-0000-000000000001")


def _handle_app_error(err: AppError) -> HTTPException:
    """Convert an AppError to an HTTPException."""
    status_map: dict[str, int] = {
        "OPPORTUNITY_NOT_FOUND": 404,
        "INVALID_ACTION_TYPE": 422,
    }
    status = status_map.get(err.code, 400)
    return HTTPException(
        status_code=status,
        detail=ErrorResponse(
            error_code=err.code, message=err.message
        ).model_dump(),
    )


@router.post(
    "/opportunities/{opportunity_id}/actions",
    response_model=ActionResponse,
    status_code=201,
)
def api_log_action(
    opportunity_id: _uuid.UUID,
    body: LogActionRequest,
    session: SessionDep,
) -> ActionResponse:
    """Log a user action on an opportunity."""
    user_id = _stub_current_user_id()

    try:
        action_type = ActionType(body.action_type)
    except ValueError as exc:
        raise _handle_app_error(
            AppError(
                code="INVALID_ACTION_TYPE",
                message=f"Invalid action type: {body.action_type}",
            )
        ) from exc

    try:
        action = log_action(
            session,
            opportunity_id,
            user_id,
            action_type,
            posted_url=body.posted_url,
        )
    except AppError as err:
        raise _handle_app_error(err) from err

    log.info(
        "Action logged via API",
        extra={
            "opportunity_id": str(opportunity_id),
            "action_type": body.action_type,
        },
    )
    return ActionResponse.model_validate(action)


@router.get(
    "/opportunities/{opportunity_id}/actions",
    response_model=ActionListResponse,
)
def api_get_actions(
    opportunity_id: _uuid.UUID,
    session: SessionDep,
) -> ActionListResponse:
    """Retrieve action history for an opportunity."""
    user_id = _stub_current_user_id()
    actions = get_action_history(session, opportunity_id, user_id)
    return ActionListResponse(
        actions=[ActionResponse.model_validate(a) for a in actions],
        count=len(actions),
    )


@router.get(
    "/analytics/funnel",
    response_model=FunnelResponse,
)
def api_get_funnel(
    session: SessionDep,
    platform: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> FunnelResponse:
    """Get conversion funnel analytics."""
    user_id = _stub_current_user_id()
    counts = get_funnel_counts(
        session,
        user_id,
        platform=platform,
        date_from=date_from,
        date_to=date_to,
    )
    return FunnelResponse(**counts)


@router.delete(
    "/actions/me",
    response_model=DeleteActionsResponse,
)
def api_delete_my_actions(
    session: SessionDep,
) -> DeleteActionsResponse:
    """Delete all actions for the current user (GDPR)."""
    user_id = _stub_current_user_id()
    count = delete_user_actions(session, user_id)

    log.info(
        "User deleted own actions",
        extra={"user_id": str(user_id), "deleted_count": count},
    )
    return DeleteActionsResponse(deleted_count=count)
