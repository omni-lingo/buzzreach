"""Template library API endpoints (QUALITY-003).

GET    /api/v1/templates              — list templates (global + user-owned)
GET    /api/v1/templates/{id}         — get single template
POST   /api/v1/templates              — create custom template
PUT    /api/v1/templates/{id}         — update own template
DELETE /api/v1/templates/{id}         — delete own template

All mutating endpoints require JWT auth. GET list is accessible without
auth (returns global templates only). Rate-limited.
"""

import logging
import uuid as _uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from contracts.auth.user import UserData
from contracts.quality.draft_template import (
    TemplateCreateRequest,
    TemplateListResponse,
    TemplateResponse,
    TemplateUpdateRequest,
)
from src.backend.api.auth_deps import get_current_user
from src.backend.api.rate_limit_middleware import require_rate_limit
from src.backend.api.v1.schemas import ErrorResponse
from src.backend.db.session import get_session
from src.backend.errors import AppError
from src.backend.services.quality.template_service import TemplateService

log = logging.getLogger("buzzreach.api.templates")

router = APIRouter(
    prefix="/api/v1/templates",
    tags=["templates"],
    dependencies=[Depends(require_rate_limit)],
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[UserData, Depends(get_current_user)]


def _to_response(tpl: object) -> TemplateResponse:
    """Convert a DraftTemplate ORM object to a TemplateResponse."""
    return TemplateResponse.model_validate(tpl)


_QUERY_CATEGORY: str | None = Query(default=None)
_QUERY_SEARCH: str | None = Query(default=None)
_QUERY_USER_ID: _uuid.UUID | None = Query(default=None)


@router.get("", response_model=TemplateListResponse)
def list_templates(
    session: SessionDep,
    category: str | None = _QUERY_CATEGORY,
    search: str | None = _QUERY_SEARCH,
    user_id: _uuid.UUID | None = _QUERY_USER_ID,
) -> TemplateListResponse:
    """List templates filtered by category and/or search term.

    Without user_id, returns only global templates.
    With user_id, returns global + that user's custom templates.
    """
    svc = TemplateService(session)
    items = svc.list_templates(
        user_id=user_id, category=category, search=search
    )
    return TemplateListResponse(
        items=[_to_response(t) for t in items],
        total=len(items),
    )


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(
    template_id: _uuid.UUID,
    session: SessionDep,
) -> TemplateResponse:
    """Get a single template by ID."""
    svc = TemplateService(session)
    try:
        tpl = svc.get_template(template_id)
    except AppError as exc:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error_code=exc.code, message=exc.message
            ).model_dump(),
        ) from None
    return _to_response(tpl)


@router.post("", response_model=TemplateResponse, status_code=201)
def create_template(
    body: TemplateCreateRequest,
    session: SessionDep,
    user: CurrentUser,
) -> TemplateResponse:
    """Create a custom template for the authenticated user."""
    svc = TemplateService(session)
    tpl = svc.create_template(body, user_id=user.id)
    log.info(
        "Template created via API",
        extra={"template_id": str(tpl.id), "user_id": str(user.id)},
    )
    return _to_response(tpl)


@router.put("/{template_id}", response_model=TemplateResponse)
def update_template(
    template_id: _uuid.UUID,
    body: TemplateUpdateRequest,
    session: SessionDep,
    user: CurrentUser,
) -> TemplateResponse:
    """Update a user-owned template."""
    svc = TemplateService(session)
    try:
        tpl = svc.update_template(
            template_id, body, user_id=user.id
        )
    except AppError as exc:
        status = 404 if exc.code == "TEMPLATE_NOT_FOUND" else 403
        raise HTTPException(
            status_code=status,
            detail=ErrorResponse(
                error_code=exc.code, message=exc.message
            ).model_dump(),
        ) from None
    return _to_response(tpl)


@router.delete("/{template_id}", status_code=204)
def delete_template(
    template_id: _uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
) -> None:
    """Delete a user-owned template."""
    svc = TemplateService(session)
    try:
        svc.delete_template(template_id, user_id=user.id)
    except AppError as exc:
        status = 404 if exc.code == "TEMPLATE_NOT_FOUND" else 403
        raise HTTPException(
            status_code=status,
            detail=ErrorResponse(
                error_code=exc.code, message=exc.message
            ).model_dump(),
        ) from None
