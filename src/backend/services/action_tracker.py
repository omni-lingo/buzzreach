"""Action tracking service for opportunity post-actions (FEAT-003).

Pure business logic — no HTTP concerns. Tracks user actions on
opportunities (viewed, copied, posted, archived) and provides
funnel analytics with date/platform filtering.

Uses audit log (AUDIT-002) for compliance trail on posted actions.
"""

import logging
import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from contracts.features.opportunity_action import ActionType
from src.backend.errors import AppError
from src.backend.models.metric import Metric
from src.backend.models.opportunity import Opportunity
from src.backend.models.opportunity_action import OpportunityAction
from src.backend.services.auth.audit_service import AuditService

log = logging.getLogger("buzzreach.services.action_tracker")


def log_action(
    session: Session,
    opportunity_id: uuid.UUID,
    user_id: uuid.UUID,
    action_type: ActionType,
    posted_url: str | None = None,
) -> OpportunityAction:
    """Record a user action on an opportunity.

    Args:
        session: DB session.
        opportunity_id: Target opportunity.
        user_id: Actor.
        action_type: One of viewed/copied/posted/archived.
        posted_url: Optional URL of the user's reply (for posted).

    Returns:
        The persisted OpportunityAction row.

    Raises:
        AppError: If the opportunity does not exist.
    """
    opp = session.get(Opportunity, opportunity_id)
    if opp is None:
        raise AppError(
            code="OPPORTUNITY_NOT_FOUND",
            message=f"Opportunity {opportunity_id} not found",
        )

    action = OpportunityAction(
        opportunity_id=opportunity_id,
        user_id=user_id,
        action_type=action_type,
        posted_url=posted_url,
    )
    session.add(action)
    session.flush()

    log.info(
        "Action logged",
        extra={
            "opportunity_id": str(opportunity_id),
            "user_id": str(user_id),
            "action_type": action_type,
        },
    )

    if action_type == ActionType.POSTED:
        _audit_posted(session, opportunity_id, user_id, posted_url)
        _record_posted_metric(session, opp.niche, posted_url)

    session.commit()
    return action


def _audit_posted(
    session: Session,
    opportunity_id: uuid.UUID,
    user_id: uuid.UUID,
    posted_url: str | None,
) -> None:
    """Write audit trail for posted actions."""
    audit = AuditService(session)
    summary = "Posted reply"
    if posted_url:
        summary = f"Posted reply at {posted_url}"
    audit.log(
        action="opportunity_posted",
        resource_type="opportunity",
        resource_id=str(opportunity_id),
        change_summary=summary,
        user_id=str(user_id),
    )


def _record_posted_metric(
    session: Session,
    niche: str,
    posted_url: str | None,
) -> None:
    """Record CORE-005 metrics for posted actions."""
    session.add(
        Metric(metric_name="opportunities_posted", niche=niche, value=1.0)
    )
    if posted_url:
        session.add(
            Metric(
                metric_name="reply_urls_tracked", niche=niche, value=1.0
            )
        )
    session.flush()


def get_action_history(
    session: Session,
    opportunity_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[OpportunityAction]:
    """List all actions for an opportunity by a specific user.

    Returns actions ordered by created_at ascending (oldest first).
    """
    return (
        session.query(OpportunityAction)
        .filter_by(opportunity_id=opportunity_id, user_id=user_id)
        .order_by(OpportunityAction.created_at.asc())
        .all()
    )


def get_funnel_counts(
    session: Session,
    user_id: uuid.UUID,
    platform: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> dict[str, int | float]:
    """Compute conversion funnel with distinct opportunity counts.

    Counts each opportunity at most once per action type to prevent
    double-counting (e.g., viewing the same opportunity twice counts
    as 1 viewed).

    Args:
        session: DB session.
        user_id: Filter to this user's actions.
        platform: Optional platform filter (joins Opportunity.source).
        date_from: Optional start of date range (inclusive).
        date_to: Optional end of date range (inclusive).

    Returns:
        Dict with keys: discovered, viewed, copied, posted, archived,
        conversion_rate.
    """
    query = session.query(OpportunityAction).filter(
        OpportunityAction.user_id == user_id
    )

    if platform or date_from or date_to:
        query = _apply_funnel_filters(
            session, query, platform, date_from, date_to
        )

    actions = query.all()
    return _compute_funnel(session, user_id, actions, platform)


def _apply_funnel_filters(
    session: Session,
    query: object,
    platform: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
) -> object:
    """Apply platform and date filters to the funnel query."""
    if platform:
        opp_ids_stmt = select(Opportunity.id).where(
            Opportunity.source == platform
        )
        query = query.filter(
            OpportunityAction.opportunity_id.in_(opp_ids_stmt)
        )
    if date_from:
        query = query.filter(
            OpportunityAction.created_at >= date_from
        )
    if date_to:
        query = query.filter(OpportunityAction.created_at <= date_to)
    return query


def _compute_funnel(
    session: Session,
    user_id: uuid.UUID,
    actions: list[OpportunityAction],
    platform: str | None,
) -> dict[str, int | float]:
    """Build funnel dict from action rows with distinct counting."""
    by_type: dict[str, set[uuid.UUID]] = {
        "viewed": set(),
        "copied": set(),
        "posted": set(),
        "archived": set(),
    }
    for action in actions:
        t = action.action_type
        if t in by_type:
            by_type[t].add(action.opportunity_id)

    viewed = len(by_type["viewed"])
    posted = len(by_type["posted"])
    rate = posted / viewed if viewed > 0 else 0.0

    discovered = _count_discovered(session, platform)

    return {
        "discovered": discovered,
        "viewed": viewed,
        "copied": len(by_type["copied"]),
        "posted": posted,
        "archived": len(by_type["archived"]),
        "conversion_rate": rate,
    }


def _count_discovered(
    session: Session, platform: str | None
) -> int:
    """Count total opportunities (optionally filtered by platform)."""
    q = session.query(func.count(Opportunity.id))
    if platform:
        q = q.filter(Opportunity.source == platform)
    return q.scalar() or 0


def delete_user_actions(
    session: Session,
    user_id: uuid.UUID,
) -> int:
    """Delete all actions for a user (GDPR compliance).

    Returns the number of rows deleted.
    """
    count = (
        session.query(OpportunityAction)
        .filter_by(user_id=user_id)
        .delete()
    )
    session.commit()

    log.info(
        "User actions deleted",
        extra={"user_id": str(user_id), "deleted_count": count},
    )
    return count
