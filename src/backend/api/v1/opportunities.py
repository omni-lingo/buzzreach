"""Opportunities API endpoints (API-001).

GET /api/v1/opportunities — list with optional niche/status filters.
POST /api/v1/opportunities/{id}/act — mark opportunity as acted.
POST /api/v1/opportunities/{id}/skip — mark opportunity as skipped.

All endpoints require JWT authentication and are rate-limited.
Act/skip actions are audit-logged.
"""

import logging
import uuid as _uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from contracts.auth.user import UserData
from src.backend.api.auth_deps import get_current_user
from src.backend.api.rate_limit_middleware import require_rate_limit
from src.backend.api.v1.schemas import ErrorResponse, OpportunityResponse
from src.backend.db.session import get_session
from src.backend.models.opportunity import Opportunity, OpportunityStatus
from src.backend.services.auth.audit_service import AuditService

log = logging.getLogger("buzzreach.api.v1.opportunities")

router = APIRouter(
    prefix="/api/v1/opportunities",
    tags=["opportunities"],
    dependencies=[Depends(require_rate_limit)],
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[UserData, Depends(get_current_user)]


@router.get(
    "",
    response_model=list[OpportunityResponse],
)
def list_opportunities(
    session: SessionDep,
    user: CurrentUser,
    niche: str | None = None,
    status: str | None = None,
) -> list[OpportunityResponse]:
    """List opportunities with optional filters."""
    query = session.query(Opportunity)

    if niche is not None:
        query = query.filter(Opportunity.niche == niche)
    if status is not None:
        query = query.filter(Opportunity.status == OpportunityStatus(status))

    rows = query.all()
    log.info(
        "Opportunities listed",
        extra={"user_id": str(user.id), "count": len(rows)},
    )
    return [OpportunityResponse.model_validate(r) for r in rows]


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


@router.post(
    "/{opportunity_id}/act",
    response_model=OpportunityResponse,
)
def act_on_opportunity(
    opportunity_id: _uuid.UUID,
    request: Request,
    session: SessionDep,
    user: CurrentUser,
) -> OpportunityResponse:
    """Mark an opportunity as acted and audit-log the action."""
    opp = _get_opportunity_or_404(session, opportunity_id)
    opp.status = OpportunityStatus.ACTED

    _audit_log(
        session=session,
        action="opportunity_acted",
        resource_id=str(opp.id),
        user_id=str(user.id),
        ip_address=_client_ip(request),
    )

    session.commit()
    log.info(
        "Opportunity acted",
        extra={"opportunity_id": str(opp.id), "user_id": str(user.id)},
    )
    return OpportunityResponse.model_validate(opp)


@router.post(
    "/{opportunity_id}/skip",
    response_model=OpportunityResponse,
)
def skip_opportunity(
    opportunity_id: _uuid.UUID,
    request: Request,
    session: SessionDep,
    user: CurrentUser,
) -> OpportunityResponse:
    """Mark an opportunity as skipped and audit-log the action."""
    opp = _get_opportunity_or_404(session, opportunity_id)
    opp.status = OpportunityStatus.SKIPPED

    _audit_log(
        session=session,
        action="opportunity_skipped",
        resource_id=str(opp.id),
        user_id=str(user.id),
        ip_address=_client_ip(request),
    )

    session.commit()
    log.info(
        "Opportunity skipped",
        extra={"opportunity_id": str(opp.id), "user_id": str(user.id)},
    )
    return OpportunityResponse.model_validate(opp)


def _audit_log(
    session: Session,
    action: str,
    resource_id: str,
    user_id: str,
    ip_address: str | None,
) -> None:
    """Write an audit log entry via AuditService."""
    audit = AuditService(session)
    audit.log(
        action=action,
        resource_type="opportunity",
        resource_id=resource_id,
        user_id=user_id,
        ip_address=ip_address,
    )


def _client_ip(request: Request) -> str | None:
    """Extract client IP from request."""
    return request.client.host if request.client else None
