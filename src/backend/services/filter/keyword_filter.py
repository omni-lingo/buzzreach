"""Keyword pre-filter: free string-match stage (FILT-002).

Per AD-6, this runs after dedup and before Haiku scoring to keep AI
cost down. Pure function — zero network, zero AI, zero I/O.

Consumed by PIPE-001 as stage 3 of the pipeline.
"""

import logging

from contracts.config.product_config import ProductConfig
from contracts.discovery.candidate import Candidate

log = logging.getLogger("buzzreach")


def keyword_match(
    candidates: list[Candidate],
    config: ProductConfig,
) -> list[Candidate]:
    """Keep only candidates whose title or snippet contains a keyword.

    Case-insensitive substring match of each keyword in
    ``config.keywords`` against the concatenation of a candidate's
    ``title`` and ``snippet``.

    Args:
        candidates: Search results to filter.
        config: Product configuration containing the keyword list.

    Returns:
        Candidates where at least one keyword matched.
    """
    if not candidates:
        return []

    lower_keywords = [kw.lower() for kw in config.keywords]
    matched = [c for c in candidates if _has_keyword(c, lower_keywords)]

    log.info(
        "Keyword pre-filter applied",
        extra={
            "total": len(candidates),
            "matched": len(matched),
            "dropped": len(candidates) - len(matched),
        },
    )

    return matched


def _has_keyword(candidate: Candidate, lower_keywords: list[str]) -> bool:
    """Return True if any keyword appears in candidate title or snippet."""
    text = f"{candidate.title} {candidate.snippet}".lower()
    return any(kw in text for kw in lower_keywords)
