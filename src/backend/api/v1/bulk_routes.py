"""Bulk opportunity endpoints (FEAT-006).

POST /api/v1/opportunities/bulk/archive  — archive multiple
POST /api/v1/opportunities/bulk/regenerate — regenerate drafts
POST /api/v1/opportunities/bulk/export — return CSV
DELETE /api/v1/opportunities/bulk — soft-delete

All endpoints require JWT authentication and are rate-limited.
Bulk actions are audit-logged.
"""

import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from contracts.auth.user import UserData
from src.backend.api.auth_deps import get_current_user
from src.backend.api.rate_limit_middleware import require_rate_limit
from src.backend.api.v1.bulk_schemas import (
    BulkIdsRequest,
    BulkResultResponse,
)
from src.backend.db.session import get_session
from src.backend.errors import AppError
from src.backend.services.bulk_actions import (
    bulk_archive,
    bulk_delete,
    bulk_export_csv,
    bulk_regenerate,
)

log = logging.getLogger("buzzreach.api.v1.bulk")

router = APIRouter(
    prefix="/api/v1/opportunities/bulk",
    tags=["bulk-actions"],
    dependencies=[Depends(require_rate_limit)],
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[UserData, Depends(get_current_user)]


@router.post("/archive", response_model=BulkResultResponse)
def archive_bulk(
    body: BulkIdsRequest,
    session: SessionDep,
    user: CurrentUser,
) -> BulkResultResponse:
    """Archive multiple opportunities."""
    result = _run_bulk(
        lambda: bulk_archive(session, body.opportunity_ids, user.id)
    )
    return BulkResultResponse(
        processed=result.processed,
        failed=result.failed,
        action=result.action,
    )


@router.post("/regenerate", response_model=BulkResultResponse)
def regenerate_bulk(
    body: BulkIdsRequest,
    session: SessionDep,
    user: CurrentUser,
) -> BulkResultResponse:
    """Regenerate drafts for multiple opportunities."""
    result = _run_bulk(
        lambda: bulk_regenerate(session, body.opportunity_ids, user.id)
    )
    return BulkResultResponse(
        processed=result.processed,
        failed=result.failed,
        action=result.action,
    )


@router.post("/export")
def export_bulk(
    body: BulkIdsRequest,
    session: SessionDep,
    user: CurrentUser,
) -> StreamingResponse:
    """Export selected opportunities as CSV download."""
    try:
        csv_content = bulk_export_csv(
            session, body.opportunity_ids, user.id
        )
    except AppError as exc:
        raise HTTPException(
            status_code=404,
            detail={"error_code": exc.code, "message": exc.message},
        ) from None

    filename = _export_filename()
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )


@router.delete("", response_model=BulkResultResponse)
def delete_bulk(
    body: BulkIdsRequest,
    session: SessionDep,
    user: CurrentUser,
) -> BulkResultResponse:
    """Soft-delete multiple opportunities."""
    result = _run_bulk(
        lambda: bulk_delete(session, body.opportunity_ids, user.id)
    )
    return BulkResultResponse(
        processed=result.processed,
        failed=result.failed,
        action=result.action,
    )


def _export_filename() -> str:
    """Generate CSV filename with current date."""
    date_str = datetime.now(UTC).strftime("%Y-%m-%d")
    return f"opportunities_{date_str}.csv"


def _run_bulk(
    action: object,
) -> object:
    """Run a bulk service call, converting AppError to HTTPException."""
    try:
        return action()  # type: ignore[operator]
    except AppError as exc:
        raise HTTPException(
            status_code=404,
            detail={"error_code": exc.code, "message": exc.message},
        ) from None
