"""Bulk actions service for opportunities (FEAT-006).

Pure business logic — no HTTP concerns. Handles archive, regenerate,
export, and soft-delete operations on multiple opportunities at once.
Audit-logged for compliance.
"""

import csv
import io
import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from contracts.features.bulk_action import BulkActionResult
from src.backend.errors import AppError
from src.backend.models.opportunity import Opportunity, OpportunityStatus
from src.backend.services.auth.audit_service import AuditService

log = logging.getLogger("buzzreach.services.bulk_actions")

_CSV_COLUMNS = [
    "URL",
    "Title",
    "Platform",
    "Score",
    "Draft",
    "Status",
    "Date",
]


def bulk_archive(
    session: Session,
    opportunity_ids: list[uuid.UUID],
    user_id: uuid.UUID,
) -> BulkActionResult:
    """Archive multiple opportunities (hide from feed, keep history)."""
    opps = _fetch_opportunities(session, opportunity_ids)
    processed = 0
    for opp in opps:
        opp.status = OpportunityStatus.SKIPPED
        processed += 1

    _audit_bulk(session, "bulk_archive", opportunity_ids, user_id)
    session.commit()

    log.info(
        "Bulk archive completed",
        extra={"user_id": str(user_id), "count": processed},
    )
    return BulkActionResult(
        processed=processed,
        failed=len(opportunity_ids) - processed,
        action="archive",
    )


def bulk_regenerate(
    session: Session,
    opportunity_ids: list[uuid.UUID],
    user_id: uuid.UUID,
) -> BulkActionResult:
    """Mark opportunities for draft regeneration (batch).

    Resets edited_draft to None so the pipeline re-generates drafts.
    Actual AI regeneration is handled by the pipeline/job layer.
    """
    opps = _fetch_opportunities(session, opportunity_ids)
    processed = 0
    for opp in opps:
        opp.edited_draft = None
        processed += 1

    _audit_bulk(session, "bulk_regenerate", opportunity_ids, user_id)
    session.commit()

    log.info(
        "Bulk regenerate queued",
        extra={"user_id": str(user_id), "count": processed},
    )
    return BulkActionResult(
        processed=processed,
        failed=len(opportunity_ids) - processed,
        action="regenerate",
    )


def bulk_export_csv(
    session: Session,
    opportunity_ids: list[uuid.UUID],
    user_id: uuid.UUID,
) -> str:
    """Export selected opportunities as CSV string."""
    opps = _fetch_opportunities(session, opportunity_ids)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(_CSV_COLUMNS)

    for opp in opps:
        writer.writerow(_format_csv_row(opp))

    _audit_bulk(session, "bulk_export", opportunity_ids, user_id)
    session.commit()

    log.info(
        "Bulk export completed",
        extra={"user_id": str(user_id), "count": len(opps)},
    )
    return output.getvalue()


def bulk_delete(
    session: Session,
    opportunity_ids: list[uuid.UUID],
    user_id: uuid.UUID,
) -> BulkActionResult:
    """Soft-delete opportunities (set status, keep records)."""
    opps = _fetch_opportunities(session, opportunity_ids)
    processed = 0
    for opp in opps:
        opp.status = OpportunityStatus.SKIPPED
        opp.delivered_at = datetime.now(UTC)
        processed += 1

    _audit_bulk(session, "bulk_delete", opportunity_ids, user_id)
    session.commit()

    log.info(
        "Bulk delete completed",
        extra={"user_id": str(user_id), "count": processed},
    )
    return BulkActionResult(
        processed=processed,
        failed=len(opportunity_ids) - processed,
        action="delete",
    )


def _fetch_opportunities(
    session: Session,
    ids: list[uuid.UUID],
) -> list[Opportunity]:
    """Fetch opportunities by IDs, raise if none found."""
    opps = (
        session.query(Opportunity)
        .filter(Opportunity.id.in_(ids))
        .all()
    )
    if not opps:
        raise AppError(
            code="NO_OPPORTUNITIES_FOUND",
            message="None of the specified opportunities exist",
        )
    return opps


def _format_csv_row(opp: Opportunity) -> list[str]:
    """Format a single opportunity as a CSV row."""
    score = f"{opp.relevance_score * 100:.0f}%"
    draft = opp.edited_draft or opp.draft_reply
    created = opp.created_at.strftime("%Y-%m-%d")
    return [
        opp.url,
        opp.title,
        opp.source,
        score,
        draft,
        opp.status.value,
        created,
    ]


def _audit_bulk(
    session: Session,
    action: str,
    ids: list[uuid.UUID],
    user_id: uuid.UUID,
) -> None:
    """Write audit log for a bulk action."""
    audit = AuditService(session)
    id_list = ", ".join(str(i) for i in ids[:5])
    suffix = f" (+{len(ids) - 5} more)" if len(ids) > 5 else ""
    audit.log(
        action=action,
        resource_type="opportunity",
        resource_id=id_list + suffix,
        change_summary=f"{action} on {len(ids)} opportunities",
        user_id=str(user_id),
    )
