"""Tiered pipeline orchestrator (PIPE-001).

Executes the full pipeline per AD-6 stage order:
  discover -> dedup (SQL) -> keyword pre-filter -> extract
  -> Haiku score -> (gate) -> Sonnet draft -> persist Opportunity
  -> audit log -> mark_seen

All dependencies are injected via ``PipelineDeps`` so each stage
is independently mockable.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from contracts.config.product_config import ProductConfig
from contracts.discovery.candidate import Candidate
from contracts.extraction.extracted_content import ExtractedContent
from contracts.opportunity.opportunity import OpportunityData
from contracts.scoring.relevance import RelevanceResult
from src.backend.models.opportunity import Opportunity
from src.backend.services.pipeline.stages import (
    passes_gate,
    run_dedup,
    run_discovery,
    run_drafting,
    run_extraction,
    run_keyword_filter,
    run_scoring,
)

log = logging.getLogger("buzzreach.pipeline")


@dataclass
class PipelineDeps:
    """Injected dependencies for the pipeline runner.

    Each field is a callable or service instance. The runner never
    imports directly from other modules' internals.
    """

    discover_fn: Callable[..., list[Candidate]]
    filter_unseen_fn: Callable[..., list[Candidate]]
    keyword_match_fn: Callable[..., list[Candidate]]
    extract_fn: Callable[..., ExtractedContent]
    score_fn: Callable[..., RelevanceResult]
    draft_fn: Callable[..., str]
    mark_seen_fn: Callable[..., None]
    audit_service: Any
    metrics_recorder: Any


def run_pipeline(
    config: ProductConfig,
    deps: PipelineDeps,
    session: Session,
) -> list[OpportunityData]:
    """Execute the full pipeline for a product configuration.

    Returns a list of OpportunityData for each candidate that
    survived all stages and had a draft generated.
    """
    candidates = run_discovery(config, deps)
    _record_candidates_found(deps, config.niche, len(candidates))

    candidates = run_dedup(candidates, config, deps, session)
    candidates = run_keyword_filter(candidates, config, deps)

    if not candidates:
        return []

    return _process_candidates(candidates, config, deps, session)


def _process_candidates(
    candidates: list[Candidate],
    config: ProductConfig,
    deps: PipelineDeps,
    session: Session,
) -> list[OpportunityData]:
    """Extract, score, gate, draft, and persist each candidate."""
    results: list[OpportunityData] = []
    for candidate in candidates:
        result = _process_single(candidate, config, deps, session)
        if result is not None:
            results.append(result)
    return results


def _process_single(
    candidate: Candidate,
    config: ProductConfig,
    deps: PipelineDeps,
    session: Session,
) -> OpportunityData | None:
    """Run extract -> score -> gate -> draft -> persist for one candidate."""
    content = run_extraction(candidate, deps)
    if content is None:
        return None

    score_result = run_scoring(content, config, deps)
    if not passes_gate(score_result):
        log.info(
            "Candidate did not pass gate",
            extra={"url": candidate.url, "reason": score_result.reason},
        )
        return None

    draft = run_drafting(content, config, deps)
    return _persist_opportunity(
        candidate, config, score_result, draft, deps, session,
    )


def _persist_opportunity(
    candidate: Candidate,
    config: ProductConfig,
    score_result: RelevanceResult,
    draft: str,
    deps: PipelineDeps,
    session: Session,
) -> OpportunityData:
    """Persist the Opportunity row, log audit event, and mark seen."""
    opp = Opportunity(
        niche=config.niche,
        url=candidate.url,
        title=candidate.title,
        source=candidate.source,
        why_matched=score_result.reason,
        relevance_score=score_result.score,
        draft_reply=draft,
    )
    session.add(opp)
    session.flush()

    _log_audit(deps, config.niche, draft)
    _mark_url_seen(deps, candidate.url, config.niche, score_result)
    _record_draft_metrics(deps, config.niche)

    return OpportunityData.model_validate(opp)


def _log_audit(
    deps: PipelineDeps, niche: str, draft: str,
) -> None:
    """Log an audit event for the generated opportunity."""
    deps.audit_service.log(
        action="opportunity_generated",
        resource_type="opportunity",
        change_summary=f"niche={niche}, draft_len={len(draft)}",
    )


def _mark_url_seen(
    deps: PipelineDeps,
    url: str,
    niche: str,
    score_result: RelevanceResult,
) -> None:
    """Mark the URL as seen with the angle covered."""
    deps.mark_seen_fn(
        url=url,
        niche=niche,
        angle_covered=score_result.reason,
    )


def _record_candidates_found(
    deps: PipelineDeps, niche: str, count: int,
) -> None:
    """Record the number of candidates found."""
    deps.metrics_recorder.record("candidates_found", float(count), niche)


def _record_draft_metrics(
    deps: PipelineDeps, niche: str,
) -> None:
    """Record metrics for a generated draft."""
    deps.metrics_recorder.record("drafts_generated", 1.0, niche)
