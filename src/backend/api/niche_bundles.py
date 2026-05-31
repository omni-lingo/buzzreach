"""Niche bundles API endpoints (QUALITY-004).

GET  /api/v1/niche-bundles          — list all available bundles
GET  /api/v1/niche-bundles/{id}     — get single bundle details
POST /api/v1/niche-bundles/apply    — apply bundle as search profile

List endpoint is public. Apply requires auth (creates a profile).
"""

import logging
import uuid as _uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from contracts.quality.niche_bundle import (
    ApplyBundleRequest,
    ApplyBundleResponse,
    NicheBundleData,
    NicheBundleListResponse,
)
from src.backend.api.auth_deps import get_current_user
from src.backend.api.rate_limit_middleware import require_rate_limit
from src.backend.api.v1.schemas import ErrorResponse
from src.backend.db.session import get_session
from src.backend.errors import AppError
from src.backend.services.quality.niche_bundle_service import (
    NicheBundleService,
)

log = logging.getLogger("buzzreach.api.niche_bundles")

router = APIRouter(
    prefix="/api/v1/niche-bundles",
    tags=["niche-bundles"],
    dependencies=[Depends(require_rate_limit)],
)

SessionDep = Annotated[Session, Depends(get_session)]


def _to_response(bundle: object) -> NicheBundleData:
    """Convert a NicheBundle ORM object to contract response."""
    return NicheBundleData.model_validate(bundle)


@router.get("", response_model=NicheBundleListResponse)
def list_bundles(session: SessionDep) -> NicheBundleListResponse:
    """List all available niche bundles."""
    svc = NicheBundleService(session)
    items = svc.list_bundles()
    return NicheBundleListResponse(
        items=[_to_response(b) for b in items],
        total=len(items),
    )


@router.get("/{bundle_id}", response_model=NicheBundleData)
def get_bundle(
    bundle_id: _uuid.UUID,
    session: SessionDep,
) -> NicheBundleData:
    """Get a single niche bundle by ID."""
    svc = NicheBundleService(session)
    try:
        bundle = svc.get_bundle(bundle_id)
    except AppError as exc:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error_code=exc.code, message=exc.message
            ).model_dump(),
        ) from None
    return _to_response(bundle)


@router.post(
    "/apply",
    response_model=ApplyBundleResponse,
    status_code=201,
)
def apply_bundle(
    body: ApplyBundleRequest,
    session: SessionDep,
    user: Annotated[object, Depends(get_current_user)],
) -> ApplyBundleResponse:
    """Apply a niche bundle to create a search profile."""
    svc = NicheBundleService(session)
    try:
        result = svc.apply_bundle(body, user_id=user.id)
    except AppError as exc:
        status = 404 if exc.code == "BUNDLE_NOT_FOUND" else 400
        raise HTTPException(
            status_code=status,
            detail=ErrorResponse(
                error_code=exc.code, message=exc.message
            ).model_dump(),
        ) from None

    log.info(
        "Bundle applied via API",
        extra={
            "bundle_id": str(body.bundle_id),
            "profile_id": str(result.profile_id),
            "user_id": str(user.id),
        },
    )
    return result
