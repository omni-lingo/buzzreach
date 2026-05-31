"""Draft editing & regeneration API endpoints (FEAT-001).

PUT  /api/v1/opportunities/{id}/draft       — save edited draft
DELETE /api/v1/opportunities/{id}/draft     — discard edits (revert)
POST /api/v1/opportunities/{id}/regenerate  — AI re-draft with tone param

All endpoints require JWT authentication, are rate-limited, and audit-logged.
"""

import logging
import uuid as _uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from contracts.auth.user import UserData
from contracts.config.product_config import ProductConfig
from contracts.extraction.extracted_content import ExtractedContent
from contracts.features.draft_edit import (
    DraftEditRequest,
    DraftRegenerateRequest,
    DraftResponse,
)
from src.backend.api.auth_deps import get_current_user
from src.backend.api.rate_limit_middleware import require_rate_limit
from src.backend.api.v1.schemas import ErrorResponse
from src.backend.db.session import get_session
from src.backend.models.opportunity import Opportunity
from src.backend.services.ai.client import AiClient
from src.backend.services.ai.draft import regenerate_draft
from src.backend.services.auth.audit_service import AuditService
from src.backend.settings import Settings

log = logging.getLogger("buzzreach.api.v1.draft")

router = APIRouter(
    prefix="/api/v1/opportunities",
    tags=["draft"],
    dependencies=[Depends(require_rate_limit)],
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[UserData, Depends(get_current_user)]


def _get_opportunity_or_404(
    session: Session,
    opportunity_id: _uuid.UUID,
) -> Opportunity:
    """Fetch an opportunity by ID or raise 404."""
    opp = session.get(Opportunity, opportunity_id)
    if opp is None:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error_code="OPPORTUNITY_NOT_FOUND",
                message="Opportunity not found",
            ).model_dump(),
        )
    return opp


def _audit_log(
    session: Session,
    action: str,
    resource_id: str,
    user_id: str,
    ip_address: str | None,
    change_summary: str | None = None,
) -> None:
    """Write an audit log entry via AuditService."""
    audit = AuditService(session)
    audit.log(
        action=action,
        resource_type="opportunity",
        resource_id=resource_id,
        user_id=user_id,
        ip_address=ip_address,
        change_summary=change_summary,
    )


def _build_draft_response(opp: Opportunity) -> DraftResponse:
    """Build a DraftResponse from an Opportunity row."""
    current = opp.edited_draft if opp.edited_draft else opp.draft_reply
    return DraftResponse(
        original_draft=opp.draft_reply,
        edited_draft=opp.edited_draft,
        current_text=current,
    )


def _client_ip(request: Request) -> str | None:
    """Extract client IP from request."""
    return request.client.host if request.client else None


def _save_draft_logic(
    opp: Opportunity,
    body: DraftEditRequest,
    session: Session,
    user_id: str,
    ip_address: str | None,
) -> DraftResponse:
    """Core logic for saving an edited draft (testable without HTTP)."""
    opp.edited_draft = body.edited_text
    _audit_log(
        session=session,
        action="draft_edited",
        resource_id=str(opp.id),
        user_id=user_id,
        ip_address=ip_address,
        change_summary=f"Draft edited ({len(body.edited_text)} chars)",
    )
    session.commit()
    log.info(
        "Draft saved",
        extra={"opportunity_id": str(opp.id), "user_id": user_id},
    )
    return _build_draft_response(opp)


@router.put(
    "/{opportunity_id}/draft",
    response_model=DraftResponse,
)
def save_draft(
    opportunity_id: _uuid.UUID,
    body: DraftEditRequest,
    request: Request,
    session: SessionDep,
    user: CurrentUser,
) -> DraftResponse:
    """Save a user-edited draft for an opportunity."""
    opp = _get_opportunity_or_404(session, opportunity_id)
    return _save_draft_logic(
        opp=opp,
        body=body,
        session=session,
        user_id=str(user.id),
        ip_address=_client_ip(request),
    )


def _discard_draft_logic(
    opp: Opportunity,
    session: Session,
    user_id: str,
    ip_address: str | None,
) -> DraftResponse:
    """Core logic for discarding draft edits (testable without HTTP)."""
    opp.edited_draft = None
    _audit_log(
        session=session,
        action="draft_discarded",
        resource_id=str(opp.id),
        user_id=user_id,
        ip_address=ip_address,
        change_summary="Reverted to original AI draft",
    )
    session.commit()
    log.info(
        "Draft discarded",
        extra={"opportunity_id": str(opp.id), "user_id": user_id},
    )
    return _build_draft_response(opp)


@router.delete(
    "/{opportunity_id}/draft",
    response_model=DraftResponse,
)
def discard_draft(
    opportunity_id: _uuid.UUID,
    request: Request,
    session: SessionDep,
    user: CurrentUser,
) -> DraftResponse:
    """Discard edits and revert to the original AI-generated draft."""
    opp = _get_opportunity_or_404(session, opportunity_id)
    return _discard_draft_logic(
        opp=opp,
        session=session,
        user_id=str(user.id),
        ip_address=_client_ip(request),
    )


def _build_regenerate_deps(
    opp: Opportunity,
) -> tuple[AiClient, ProductConfig, ExtractedContent]:
    """Build dependencies for draft regeneration."""
    settings = Settings()
    client = AiClient(api_key=settings.anthropic_api_key)
    config = ProductConfig(
        slug=opp.niche,
        product_url="https://example.com",
        pitch="",
        niche=opp.niche,
        keywords=[],
        tone="helpful",
        mention="",
    )
    content = ExtractedContent(
        url=opp.url,
        title=opp.title,
        body=opp.why_matched,
        comments=[],
    )
    return client, config, content


def _regenerate_draft_logic(
    opp: Opportunity,
    body: DraftRegenerateRequest,
    session: Session,
    user_id: str,
    ip_address: str | None,
) -> DraftResponse:
    """Core logic for regenerating a draft (testable without HTTP)."""
    client, config, content = _build_regenerate_deps(opp)
    new_draft = regenerate_draft(
        content=content,
        config=config,
        client=client,
        tone_override=body.tone.value,
    )
    opp.draft_reply = new_draft
    opp.edited_draft = None
    _audit_log(
        session=session,
        action="draft_regenerated",
        resource_id=str(opp.id),
        user_id=user_id,
        ip_address=ip_address,
        change_summary=f"Regenerated with tone: {body.tone.value}",
    )
    session.commit()
    log.info(
        "Draft regenerated",
        extra={
            "opportunity_id": str(opp.id),
            "user_id": user_id,
            "tone": body.tone.value,
        },
    )
    return _build_draft_response(opp)


@router.post(
    "/{opportunity_id}/regenerate",
    response_model=DraftResponse,
)
def regenerate_opportunity_draft(
    opportunity_id: _uuid.UUID,
    body: DraftRegenerateRequest,
    request: Request,
    session: SessionDep,
    user: CurrentUser,
) -> DraftResponse:
    """Regenerate the AI draft with a different tone."""
    opp = _get_opportunity_or_404(session, opportunity_id)
    return _regenerate_draft_logic(
        opp=opp,
        body=body,
        session=session,
        user_id=str(user.id),
        ip_address=_client_ip(request),
    )
