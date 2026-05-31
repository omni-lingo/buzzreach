"""Per-stage helpers for the pipeline orchestrator (PIPE-001).

Each function handles one pipeline stage, keeping the main runner
lean and every function under 50 lines. Stage order per AD-6:

  discover -> dedup (SQL, $0) -> keyword pre-filter ($0)
  -> extract -> Haiku score -> (gate) -> Sonnet draft
  -> persist Opportunity -> audit log -> mark_seen
"""

import logging
from typing import TYPE_CHECKING

from contracts.config.product_config import ProductConfig
from contracts.discovery.candidate import Candidate
from contracts.extraction.extracted_content import ExtractedContent
from contracts.scoring.relevance import RelevanceResult
from src.backend.errors import AppError

if TYPE_CHECKING:
    from src.backend.services.pipeline.runner import PipelineDeps

log = logging.getLogger("buzzreach.pipeline")

SCORE_THRESHOLD: float = 0.5


def run_discovery(
    config: ProductConfig,
    deps: "PipelineDeps",
) -> list[Candidate]:
    """Stage 1: Discover candidates via search."""
    candidates = deps.discover_fn(config)
    log.info(
        "Discovery stage complete",
        extra={
            "product": config.slug,
            "candidates": len(candidates),
        },
    )
    return candidates


def run_dedup(
    candidates: list[Candidate],
    config: ProductConfig,
    deps: "PipelineDeps",
    session: object,
) -> list[Candidate]:
    """Stage 2: Filter out already-seen URLs (SQL lookup, $0)."""
    unseen = deps.filter_unseen_fn(
        candidates, config.niche, session,
    )
    log.info(
        "Dedup stage complete",
        extra={
            "before": len(candidates),
            "after": len(unseen),
        },
    )
    return unseen


def run_keyword_filter(
    candidates: list[Candidate],
    config: ProductConfig,
    deps: "PipelineDeps",
) -> list[Candidate]:
    """Stage 3: Keyword pre-filter (string match, $0)."""
    matched = deps.keyword_match_fn(candidates, config)
    log.info(
        "Keyword filter stage complete",
        extra={
            "before": len(candidates),
            "after": len(matched),
        },
    )
    return matched


def run_extraction(
    candidate: Candidate,
    deps: "PipelineDeps",
) -> ExtractedContent | None:
    """Stage 4: Extract page content for a single candidate.

    Returns None if extraction fails (non-fatal per candidate).
    """
    try:
        return deps.extract_fn(candidate.url)
    except AppError:
        log.warning(
            "Extraction failed, skipping candidate",
            extra={"url": candidate.url},
        )
        return None


def run_scoring(
    content: ExtractedContent,
    config: ProductConfig,
    deps: "PipelineDeps",
) -> RelevanceResult:
    """Stage 5: Score relevance with Haiku (cheap AI, ~$0.003)."""
    return deps.score_fn(content, config)


def passes_gate(result: RelevanceResult) -> bool:
    """Check whether a score result passes the drafting gate.

    Drafting runs only when:
    - is_seeking_help is True
    - angle_already_covered is False
    - score >= SCORE_THRESHOLD
    """
    if not result.is_seeking_help:
        return False
    if result.angle_already_covered:
        return False
    return result.score >= SCORE_THRESHOLD


def run_drafting(
    content: ExtractedContent,
    config: ProductConfig,
    deps: "PipelineDeps",
) -> str:
    """Stage 6: Draft reply with Sonnet (expensive AI, ~$0.01)."""
    return deps.draft_fn(content, config)
