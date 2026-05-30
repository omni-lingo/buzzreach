"""Tests for src.backend.services.ai.scorer — Haiku relevance scoring."""

import json
from unittest.mock import MagicMock, patch

import pytest

from contracts.config.product_config import ProductConfig
from contracts.extraction.extracted_content import ExtractedContent
from contracts.scoring.relevance import RelevanceResult
from src.backend.errors import AppError
from src.backend.services.ai.client import HAIKU, AiClient
from src.backend.services.ai.scorer import score

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_client(response_text: str) -> AiClient:
    """Create an AiClient with a mocked complete() that returns response_text."""
    with patch("src.backend.services.ai.client.Anthropic"):
        client = AiClient(api_key="sk-ant-test-key")
    client.complete = MagicMock(return_value=response_text)  # type: ignore[assignment]
    return client


def _make_content() -> ExtractedContent:
    return ExtractedContent(
        url="https://reddit.com/r/tax/comments/abc123",
        title="Help with IRS CP14 notice",
        body="I received a CP14 notice and don't know what to do. "
        "The penalty is $500 and I can't afford it.",
        comments=["You should call the IRS", "Try an installment agreement"],
    )


def _make_config() -> ProductConfig:
    return ProductConfig(
        slug="irs-calculator",
        product_url="https://irscalculator.example.com",
        pitch="Calculate your IRS penalty reduction in 60 seconds",
        niche="tax",
        keywords=["IRS penalty", "CP14", "tax help"],
        tone="helpful and empathetic",
        mention="IRS Penalty Calculator",
    )


def _valid_verdict() -> dict[str, object]:
    return {
        "score": 0.85,
        "is_seeking_help": True,
        "angle_already_covered": False,
        "reason": "User is asking about CP14 penalty help, no existing comment "
        "mentions a calculator tool.",
    }


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

class TestScoreHappyPath:
    """score() returns a validated RelevanceResult for well-formed AI output."""

    def test_returns_relevance_result(self) -> None:
        verdict = _valid_verdict()
        client = _make_client(json.dumps(verdict))
        result = score(_make_content(), _make_config(), client)

        assert isinstance(result, RelevanceResult)
        assert result.score == 0.85
        assert result.is_seeking_help is True
        assert result.angle_already_covered is False
        assert "CP14" in result.reason

    def test_uses_haiku_model(self) -> None:
        verdict = _valid_verdict()
        client = _make_client(json.dumps(verdict))
        score(_make_content(), _make_config(), client)

        client.complete.assert_called_once()  # type: ignore[union-attr]
        call_kwargs = client.complete.call_args  # type: ignore[union-attr]
        assert call_kwargs.kwargs["model"] == HAIKU

    def test_score_at_boundaries(self) -> None:
        for boundary_score in [0.0, 1.0, 0.5]:
            verdict = _valid_verdict()
            verdict["score"] = boundary_score
            client = _make_client(json.dumps(verdict))
            result = score(_make_content(), _make_config(), client)
            assert result.score == boundary_score


# ---------------------------------------------------------------------------
# Score clamping
# ---------------------------------------------------------------------------

class TestScoreClamping:
    """Scores outside [0, 1] are clamped rather than crashing."""

    def test_score_above_one_clamped(self) -> None:
        verdict = _valid_verdict()
        verdict["score"] = 1.5
        client = _make_client(json.dumps(verdict))
        result = score(_make_content(), _make_config(), client)
        assert result.score == 1.0

    def test_score_below_zero_clamped(self) -> None:
        verdict = _valid_verdict()
        verdict["score"] = -0.3
        client = _make_client(json.dumps(verdict))
        result = score(_make_content(), _make_config(), client)
        assert result.score == 0.0


# ---------------------------------------------------------------------------
# Malformed AI output
# ---------------------------------------------------------------------------

class TestMalformedOutput:
    """Malformed model output raises AppError(code='AI_BAD_OUTPUT')."""

    def test_non_json_raises_app_error(self) -> None:
        client = _make_client("This is not JSON at all")
        with pytest.raises(AppError) as exc_info:
            score(_make_content(), _make_config(), client)
        assert exc_info.value.code == "AI_BAD_OUTPUT"

    def test_missing_fields_raises_app_error(self) -> None:
        incomplete = {"score": 0.5}
        client = _make_client(json.dumps(incomplete))
        with pytest.raises(AppError) as exc_info:
            score(_make_content(), _make_config(), client)
        assert exc_info.value.code == "AI_BAD_OUTPUT"

    def test_wrong_types_raises_app_error(self) -> None:
        bad_types = {
            "score": "high",
            "is_seeking_help": "yes",
            "angle_already_covered": "no",
            "reason": 42,
        }
        client = _make_client(json.dumps(bad_types))
        with pytest.raises(AppError) as exc_info:
            score(_make_content(), _make_config(), client)
        assert exc_info.value.code == "AI_BAD_OUTPUT"

    def test_empty_string_raises_app_error(self) -> None:
        client = _make_client("")
        with pytest.raises(AppError) as exc_info:
            score(_make_content(), _make_config(), client)
        assert exc_info.value.code == "AI_BAD_OUTPUT"

    def test_json_with_markdown_fences_parsed(self) -> None:
        verdict = _valid_verdict()
        fenced = f"```json\n{json.dumps(verdict)}\n```"
        client = _make_client(fenced)
        result = score(_make_content(), _make_config(), client)
        assert isinstance(result, RelevanceResult)
        assert result.score == 0.85


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

class TestPromptConstruction:
    """The prompt sent to the AI contains the right context."""

    def test_prompt_includes_content_and_config(self) -> None:
        verdict = _valid_verdict()
        client = _make_client(json.dumps(verdict))
        content = _make_content()
        config = _make_config()
        score(content, config, client)

        call_args = client.complete.call_args  # type: ignore[union-attr]
        user_prompt = call_args.kwargs["user"]

        assert content.title in user_prompt
        assert content.body in user_prompt
        assert config.pitch in user_prompt
        assert config.niche in user_prompt

    def test_prompt_includes_existing_comments(self) -> None:
        verdict = _valid_verdict()
        client = _make_client(json.dumps(verdict))
        content = _make_content()
        score(content, _make_config(), client)

        call_args = client.complete.call_args  # type: ignore[union-attr]
        user_prompt = call_args.kwargs["user"]

        for comment in content.comments:
            assert comment in user_prompt

    def test_no_comments_handled(self) -> None:
        verdict = _valid_verdict()
        client = _make_client(json.dumps(verdict))
        content = ExtractedContent(
            url="https://example.com/post",
            title="A question",
            body="Need help with something",
            comments=[],
        )
        result = score(content, _make_config(), client)
        assert isinstance(result, RelevanceResult)
