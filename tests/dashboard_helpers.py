"""Shared test helpers for DASH-001 dashboard tests.

Provides seed functions for opportunities, metrics, and error logs
used by both test_dashboard_api.py and test_dashboard_errors.py.
"""

from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.backend.models.audit_log import AuditLog
from src.backend.models.metric import Metric
from src.backend.models.opportunity import Opportunity, OpportunityStatus


def build_dashboard_client(db_session: Session) -> TestClient:
    """Build a TestClient with session override, no auth needed."""
    from src.backend.api.main import create_app
    from src.backend.db.session import get_session

    app = create_app()

    def _override_session() -> Session:
        return db_session

    app.dependency_overrides[get_session] = _override_session
    return TestClient(app)


def seed_opportunity(
    session: Session,
    niche: str = "tax-help",
    status: OpportunityStatus = OpportunityStatus.NEW,
    created_at: datetime | None = None,
) -> Opportunity:
    """Create and persist an opportunity."""
    opp = Opportunity(
        niche=niche,
        url="https://reddit.com/r/tax/123",
        title="Need help with IRS penalty",
        source="reddit",
        why_matched="User asking about IRS penalties",
        relevance_score=0.85,
        draft_reply="Here is how you can resolve this...",
        status=status,
    )
    if created_at is not None:
        opp.created_at = created_at
    session.add(opp)
    session.commit()
    return opp


def seed_metric(
    session: Session,
    metric_name: str = "candidates_found",
    value: float = 5.0,
    niche: str = "tax-help",
    timestamp: datetime | None = None,
) -> Metric:
    """Create and persist a metric row."""
    row = Metric(
        metric_name=metric_name,
        value=value,
        niche=niche,
    )
    if timestamp is not None:
        row.timestamp = timestamp
    session.add(row)
    session.commit()
    return row


def seed_error_log(
    session: Session,
    action: str = "pipeline_error",
    resource_type: str = "pipeline",
    change_summary: str = "Search API timed out",
    created_at: datetime | None = None,
) -> AuditLog:
    """Create and persist an error audit log entry."""
    entry = AuditLog(
        action=action,
        resource_type=resource_type,
        change_summary=change_summary,
    )
    if created_at is not None:
        entry.created_at = created_at
    session.add(entry)
    session.commit()
    return entry
