"""Digest builder for the delivery module (DELIV-001).

Renders a list of OpportunityData into a plain-text + HTML digest ready
for email or Slack delivery. Also provides fetch_new_opportunities to
query the database for undelivered opportunities.
"""

import logging
from html import escape

from sqlalchemy.orm import Session

from contracts.delivery.digest import Digest
from contracts.opportunity.opportunity import OpportunityData
from src.backend.models.opportunity import Opportunity, OpportunityStatus

log = logging.getLogger("buzzreach")


def build_digest(opportunities: list[OpportunityData]) -> Digest:
    """Render opportunities into a Digest with text and HTML bodies.

    Args:
        opportunities: List of opportunity DTOs to include.

    Returns:
        A Digest with subject, text_body, html_body, and opportunity_ids.
    """
    if not opportunities:
        return _build_empty_digest()

    subject = f"BuzzReach: {len(opportunities)} new opportunities"
    text_body = _render_text_body(opportunities)
    html_body = _render_html_body(opportunities)
    ids = [opp.id for opp in opportunities]

    log.info(
        "Digest built",
        extra={"opportunity_count": len(opportunities)},
    )

    return Digest(
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        opportunity_ids=ids,
    )


def fetch_new_opportunities(
    session: Session,
    niche: str | None = None,
) -> list[OpportunityData]:
    """Fetch opportunities with status='new', optionally filtered by niche.

    Args:
        session: SQLAlchemy session.
        niche: If provided, only return opportunities for this niche.

    Returns:
        List of OpportunityData DTOs for undelivered opportunities.
    """
    query = session.query(Opportunity).filter(
        Opportunity.status == OpportunityStatus.NEW,
    )
    if niche is not None:
        query = query.filter(Opportunity.niche == niche)

    rows = query.all()

    log.info(
        "Fetched new opportunities",
        extra={"count": len(rows), "niche": niche},
    )

    return [
        OpportunityData.model_validate(row, from_attributes=True)
        for row in rows
    ]


def _build_empty_digest() -> Digest:
    """Build a valid digest when there are no opportunities."""
    return Digest(
        subject="BuzzReach: No new opportunities",
        text_body="No new opportunities found. Check back later.",
        html_body="<p>No new opportunities found. Check back later.</p>",
        opportunity_ids=[],
    )


def _render_text_body(opportunities: list[OpportunityData]) -> str:
    """Render the plain-text version of the digest."""
    sections: list[str] = []
    for i, opp in enumerate(opportunities, start=1):
        section = (
            f"--- Opportunity {i} ---\n"
            f"URL: {opp.url}\n"
            f"Score: {opp.relevance_score}\n"
            f"Why matched: {opp.why_matched}\n"
            f"\nDraft reply:\n{opp.draft_reply}\n"
        )
        sections.append(section)
    return "\n".join(sections)


def _render_html_body(opportunities: list[OpportunityData]) -> str:
    """Render the HTML version of the digest."""
    items: list[str] = []
    for opp in opportunities:
        item = (
            "<div style='margin-bottom:20px;'>"
            f"<h3><a href='{escape(opp.url)}'>{escape(opp.title)}</a></h3>"
            f"<p><strong>Score:</strong> {opp.relevance_score}</p>"
            f"<p><strong>Why matched:</strong> {escape(opp.why_matched)}</p>"
            f"<p><strong>Draft reply:</strong></p>"
            f"<blockquote>{escape(opp.draft_reply)}</blockquote>"
            "</div>"
        )
        items.append(item)

    body = (
        "<html><body>"
        "<h1>BuzzReach Digest</h1>"
        + "".join(items)
        + "</body></html>"
    )
    return body
