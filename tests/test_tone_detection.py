"""Tests for src.backend.services.tone_detector — Tone Detection (FEAT-005).

Covers: reading level, marketing score, AI likelihood, authenticity,
warnings, edge cases, and performance.
"""

import time

from contracts.features.tone_analysis import ToneMetrics
from src.backend.services.tone_detector import analyze_tone

# ---------------------------------------------------------------------------
# Sample texts
# ---------------------------------------------------------------------------

CASUAL_HELPFUL = (
    "Hey, I had the same issue last year. What worked for me was calling "
    "the IRS directly and asking about penalty abatement. They were "
    "surprisingly helpful. You might also want to check out this penalty "
    "calculator I found — it helped me figure out what I actually owed."
)

SALESY_TEXT = (
    "BUY NOW! Limited time offer — don't miss out on this exclusive deal! "
    "Act fast before this amazing opportunity disappears forever! "
    "Order today and get FREE shipping! Click here to purchase NOW! "
    "This incredible product will change your life guaranteed!"
)

AI_ROBOTIC = (
    "In conclusion, it is important to note that there are several "
    "factors to consider when evaluating this situation. Furthermore, "
    "it is worth mentioning that the aforementioned approach has been "
    "extensively documented in the literature. Additionally, one must "
    "take into account the various implications and ramifications of "
    "the proposed methodology."
)

SIMPLE_TEXT = "I like cats. Cats are fun. I have two cats at home."

DENSE_ACADEMIC = (
    "The epistemological ramifications of quantum superposition "
    "necessitate a fundamental reconceptualization of ontological "
    "presuppositions undergirding contemporary hermeneutical "
    "frameworks within the phenomenological tradition of "
    "transcendental idealism and its dialectical counterpart."
)

EMPTY_TEXT = ""

SHORT_TEXT = "Hi"


# ---------------------------------------------------------------------------
# Reading level
# ---------------------------------------------------------------------------

class TestReadingLevel:
    """Reading level uses Flesch-Kincaid grade level."""

    def test_simple_text_low_reading_level(self) -> None:
        result = analyze_tone(SIMPLE_TEXT)
        assert result.reading_level < 6.0

    def test_casual_text_moderate_reading_level(self) -> None:
        result = analyze_tone(CASUAL_HELPFUL)
        assert 4.0 <= result.reading_level <= 14.0

    def test_dense_text_high_reading_level(self) -> None:
        result = analyze_tone(DENSE_ACADEMIC)
        assert result.reading_level > 12.0

    def test_empty_text_returns_zero(self) -> None:
        result = analyze_tone(EMPTY_TEXT)
        assert result.reading_level == 0.0

    def test_short_text_no_crash(self) -> None:
        result = analyze_tone(SHORT_TEXT)
        assert result.reading_level >= 0.0


# ---------------------------------------------------------------------------
# Marketing score
# ---------------------------------------------------------------------------

class TestMarketingScore:
    """Marketing score detects salesy language."""

    def test_salesy_text_high_score(self) -> None:
        result = analyze_tone(SALESY_TEXT)
        assert result.marketing_score > 0.7

    def test_casual_text_low_score(self) -> None:
        result = analyze_tone(CASUAL_HELPFUL)
        assert result.marketing_score < 0.5

    def test_empty_text_zero_score(self) -> None:
        result = analyze_tone(EMPTY_TEXT)
        assert result.marketing_score == 0.0

    def test_legitimate_business_mention_low_score(self) -> None:
        text = (
            "I've been using QuickBooks for my small business and it "
            "works well for tracking expenses. Might be worth a try."
        )
        result = analyze_tone(text)
        assert result.marketing_score < 0.5


# ---------------------------------------------------------------------------
# AI likelihood
# ---------------------------------------------------------------------------

class TestAiLikelihood:
    """AI likelihood detects AI-written patterns."""

    def test_robotic_text_high_likelihood(self) -> None:
        result = analyze_tone(AI_ROBOTIC)
        assert result.ai_likelihood > 0.5

    def test_casual_text_low_likelihood(self) -> None:
        result = analyze_tone(CASUAL_HELPFUL)
        assert result.ai_likelihood < 0.5

    def test_empty_text_zero(self) -> None:
        result = analyze_tone(EMPTY_TEXT)
        assert result.ai_likelihood == 0.0


# ---------------------------------------------------------------------------
# Authenticity score
# ---------------------------------------------------------------------------

class TestAuthenticityScore:
    """Authenticity score is inverse relationship with AI likelihood."""

    def test_casual_text_high_authenticity(self) -> None:
        result = analyze_tone(CASUAL_HELPFUL)
        assert result.authenticity_score > 0.5

    def test_robotic_text_low_authenticity(self) -> None:
        result = analyze_tone(AI_ROBOTIC)
        assert result.authenticity_score < 0.5

    def test_scores_sum_near_one(self) -> None:
        result = analyze_tone(CASUAL_HELPFUL)
        total = result.ai_likelihood + result.authenticity_score
        assert 0.99 <= total <= 1.01


# ---------------------------------------------------------------------------
# Warnings
# ---------------------------------------------------------------------------

class TestWarnings:
    """Warnings fire on threshold violations."""

    def test_salesy_warning_fires(self) -> None:
        result = analyze_tone(SALESY_TEXT)
        codes = [w.code for w in result.warnings]
        assert "HIGH_MARKETING" in codes

    def test_ai_warning_fires_on_robotic_text(self) -> None:
        text = (
            "In conclusion, it is important to note that furthermore, "
            "additionally, moreover, it is worth mentioning that the "
            "aforementioned considerations are particularly relevant "
            "in the context of the broader discussion. In conclusion, "
            "it is important to note that furthermore, additionally, "
            "moreover, it is worth mentioning that one must consider."
        )
        result = analyze_tone(text)
        codes = [w.code for w in result.warnings]
        assert "AI_DETECTED" in codes

    def test_dense_reading_warning_fires(self) -> None:
        result = analyze_tone(DENSE_ACADEMIC)
        codes = [w.code for w in result.warnings]
        assert "HIGH_READING_LEVEL" in codes

    def test_casual_text_no_warnings(self) -> None:
        result = analyze_tone(CASUAL_HELPFUL)
        assert len(result.warnings) == 0

    def test_warnings_have_suggestions(self) -> None:
        result = analyze_tone(SALESY_TEXT)
        for w in result.warnings:
            assert len(w.suggestion) > 0


# ---------------------------------------------------------------------------
# Return type & contract
# ---------------------------------------------------------------------------

class TestReturnType:
    """analyze_tone returns a valid ToneMetrics contract."""

    def test_returns_tone_metrics(self) -> None:
        result = analyze_tone(CASUAL_HELPFUL)
        assert isinstance(result, ToneMetrics)

    def test_all_scores_in_range(self) -> None:
        for text in [CASUAL_HELPFUL, SALESY_TEXT, AI_ROBOTIC, SIMPLE_TEXT]:
            result = analyze_tone(text)
            assert 0.0 <= result.marketing_score <= 1.0
            assert 0.0 <= result.ai_likelihood <= 1.0
            assert 0.0 <= result.authenticity_score <= 1.0
            assert result.reading_level >= 0.0


# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------

class TestPerformance:
    """Tone analysis should be fast (< 200ms per draft)."""

    def test_analysis_under_200ms(self) -> None:
        start = time.monotonic()
        for _ in range(10):
            analyze_tone(CASUAL_HELPFUL)
        elapsed = time.monotonic() - start
        avg_ms = (elapsed / 10) * 1000
        assert avg_ms < 200
