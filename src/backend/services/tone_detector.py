"""Tone detection and quality scoring for draft text (FEAT-005).

Pure business logic — no HTTP concerns. Analyzes draft text to produce
tone metrics (reading level, marketing score, AI likelihood, authenticity)
and actionable warnings when thresholds are exceeded.

Used by:
- FEAT-001 (draft editor) for real-time feedback
- AI-002 (scorer) as quality signal
"""

import logging

from contracts.features.tone_analysis import ToneMetrics, ToneWarning
from src.backend.services.tone_analysis_helpers import (
    compute_ai_likelihood,
    compute_marketing_score,
    flesch_kincaid_grade,
)

log = logging.getLogger("buzzreach.services.tone_detector")

_MARKETING_THRESHOLD: float = 0.7
_AI_THRESHOLD: float = 0.8
_READING_LEVEL_THRESHOLD: float = 12.0


def analyze_tone(draft_text: str) -> ToneMetrics:
    """Analyze tone metrics for a piece of draft text.

    Args:
        draft_text: The draft reply text to analyze.

    Returns:
        ToneMetrics with reading_level, marketing_score,
        ai_likelihood, authenticity_score, and warnings.
    """
    reading_level = flesch_kincaid_grade(draft_text)
    marketing_score = compute_marketing_score(draft_text)
    ai_likelihood = compute_ai_likelihood(draft_text)
    authenticity_score = 1.0 - ai_likelihood
    warnings = _build_warnings(
        reading_level, marketing_score, ai_likelihood
    )

    log.info(
        "Tone analysis completed",
        extra={
            "reading_level": round(reading_level, 2),
            "marketing_score": round(marketing_score, 2),
            "ai_likelihood": round(ai_likelihood, 2),
            "warning_count": len(warnings),
        },
    )

    return ToneMetrics(
        reading_level=round(reading_level, 2),
        marketing_score=round(marketing_score, 2),
        ai_likelihood=round(ai_likelihood, 2),
        authenticity_score=round(authenticity_score, 2),
        warnings=warnings,
    )


def _build_warnings(
    reading_level: float,
    marketing_score: float,
    ai_likelihood: float,
) -> list[ToneWarning]:
    """Generate warnings when metrics exceed thresholds."""
    warnings: list[ToneWarning] = []
    if marketing_score > _MARKETING_THRESHOLD:
        warnings.append(
            ToneWarning(
                code="HIGH_MARKETING",
                message=(
                    "Draft sounds like an advertisement, "
                    "community may reject"
                ),
                suggestion=(
                    "Remove urgency words (buy, now, limited). "
                    "Lead with helpful advice instead."
                ),
            )
        )
    if ai_likelihood > _AI_THRESHOLD:
        warnings.append(
            ToneWarning(
                code="AI_DETECTED",
                message=(
                    "Draft may be detected as AI, consider editing"
                ),
                suggestion=(
                    "Break up long sentences. Use contractions "
                    "and casual language. Remove filler phrases "
                    "like 'it is important to note'."
                ),
            )
        )
    if reading_level > _READING_LEVEL_THRESHOLD:
        warnings.append(
            ToneWarning(
                code="HIGH_READING_LEVEL",
                message="Dense text, simplify for accessibility",
                suggestion=(
                    "Use shorter words and sentences. "
                    "Aim for 8th-grade reading level."
                ),
            )
        )
    return warnings
