"""Dedup service: SQL lookup against seen_urls (FILT-001).

Provides two functions consumed by the pipeline (PIPE-001):
- filter_unseen: drops candidates whose (url, niche) already exists.
- mark_seen: records a URL as seen for a niche (idempotent).

Per AD-4, dedup is a $0 SQL lookup against our own actions table —
we never cache the web, only track what we've already processed.
"""

import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from contracts.discovery.candidate import Candidate
from src.backend.models.seen_url import SeenUrl

log = logging.getLogger("buzzreach")


def filter_unseen(
    candidates: list[Candidate],
    niche: str,
    session: Session,
) -> list[Candidate]:
    """Return only candidates not yet in seen_urls for the given niche.

    Args:
        candidates: Search results to filter.
        niche: The niche context (e.g. "tax", "parking").
        session: SQLAlchemy session for the lookup.

    Returns:
        Candidates whose (url, niche) pair is not in seen_urls.
    """
    if not candidates:
        return []

    urls = [c.url for c in candidates]

    stmt = (
        select(SeenUrl.url)
        .where(SeenUrl.niche == niche)
        .where(SeenUrl.url.in_(urls))
    )
    seen_urls: set[str] = set(session.execute(stmt).scalars())

    log.info(
        "Dedup filter applied",
        extra={
            "niche": niche,
            "total": len(candidates),
            "seen": len(seen_urls),
        },
    )

    return [c for c in candidates if c.url not in seen_urls]


def mark_seen(
    url: str,
    niche: str,
    angle_covered: str | None = None,
    shown_to: str | None = None,
    session: Session | None = None,
) -> None:
    """Record a URL as seen for a niche. Idempotent on (url, niche).

    If the (url, niche) pair already exists, the call is a no-op —
    it respects the unique constraint without raising.

    Args:
        url: The URL to mark as seen.
        niche: The niche context.
        angle_covered: Optional angle/topic covered in this URL.
        shown_to: Optional user identifier the URL was shown to.
        session: SQLAlchemy session for the write.
    """
    if session is None:
        msg = "session is required"
        raise ValueError(msg)

    row = SeenUrl(
        url=url,
        niche=niche,
        angle_covered=angle_covered,
        shown_to=shown_to,
    )
    try:
        session.add(row)
        session.flush()
        session.commit()
    except IntegrityError:
        session.rollback()
        log.info(
            "URL already seen, skipping",
            extra={"url": url, "niche": niche},
        )
