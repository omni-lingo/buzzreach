"""Tests for src.backend.services.ai.draft — Sonnet draft generation."""

from unittest.mock import MagicMock, patch

from contracts.config.product_config import ProductConfig
from contracts.extraction.extracted_content import ExtractedContent
from src.backend.services.ai.client import SONNET, AiClient
from src.backend.services.ai.draft import draft_reply

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_client(response_text: str) -> AiClient:
    """Create an AiClient with a mocked complete() returning response_text."""
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


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

class TestDraftReplyHappyPath:
    """draft_reply() returns the AI-generated reply string."""

    def test_returns_reply_string(self) -> None:
        reply_text = "That sounds stressful. Have you looked into penalty abatement?"
        client = _make_client(reply_text)
        result = draft_reply(_make_content(), _make_config(), client)

        assert result == reply_text

    def test_uses_sonnet_model(self) -> None:
        client = _make_client("A helpful reply.")
        draft_reply(_make_content(), _make_config(), client)

        client.complete.assert_called_once()  # type: ignore[union-attr]
        call_kwargs = client.complete.call_args  # type: ignore[union-attr]
        assert call_kwargs.kwargs["model"] == SONNET


# ---------------------------------------------------------------------------
# Prompt construction — existing comments
# ---------------------------------------------------------------------------

class TestPromptIncludesComments:
    """The prompt includes existing comments to avoid repetition."""

    def test_prompt_includes_all_existing_comments(self) -> None:
        client = _make_client("A helpful reply.")
        content = _make_content()
        draft_reply(content, _make_config(), client)

        call_args = client.complete.call_args  # type: ignore[union-attr]
        user_prompt = call_args.kwargs["user"]

        for comment in content.comments:
            assert comment in user_prompt

    def test_no_comments_handled_gracefully(self) -> None:
        client = _make_client("A helpful reply.")
        content = ExtractedContent(
            url="https://example.com/post",
            title="A question",
            body="Need help with something",
            comments=[],
        )
        result = draft_reply(content, _make_config(), client)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Prompt construction — tone, pitch, mention, product_url
# ---------------------------------------------------------------------------

class TestPromptIncludesConfig:
    """The prompt incorporates tone, pitch, mention, and product_url."""

    def test_prompt_includes_tone(self) -> None:
        client = _make_client("Reply text.")
        config = _make_config()
        draft_reply(_make_content(), config, client)

        call_args = client.complete.call_args  # type: ignore[union-attr]
        user_prompt = call_args.kwargs["user"]
        assert config.tone in user_prompt

    def test_prompt_includes_pitch(self) -> None:
        client = _make_client("Reply text.")
        config = _make_config()
        draft_reply(_make_content(), config, client)

        call_args = client.complete.call_args  # type: ignore[union-attr]
        user_prompt = call_args.kwargs["user"]
        assert config.pitch in user_prompt

    def test_prompt_includes_mention(self) -> None:
        client = _make_client("Reply text.")
        config = _make_config()
        draft_reply(_make_content(), config, client)

        call_args = client.complete.call_args  # type: ignore[union-attr]
        user_prompt = call_args.kwargs["user"]
        assert config.mention in user_prompt

    def test_prompt_includes_product_url(self) -> None:
        client = _make_client("Reply text.")
        config = _make_config()
        draft_reply(_make_content(), config, client)

        call_args = client.complete.call_args  # type: ignore[union-attr]
        user_prompt = call_args.kwargs["user"]
        assert str(config.product_url) in user_prompt


# ---------------------------------------------------------------------------
# Prompt construction — content fields
# ---------------------------------------------------------------------------

class TestPromptIncludesContent:
    """The prompt includes the extracted page content."""

    def test_prompt_includes_title_and_body(self) -> None:
        client = _make_client("Reply text.")
        content = _make_content()
        draft_reply(content, _make_config(), client)

        call_args = client.complete.call_args  # type: ignore[union-attr]
        user_prompt = call_args.kwargs["user"]
        assert content.title in user_prompt
        assert content.body in user_prompt


# ---------------------------------------------------------------------------
# System prompt quality constraints
# ---------------------------------------------------------------------------

class TestSystemPromptConstraints:
    """The system prompt enforces key quality rules from BUZZREACH.md §6."""

    def test_system_prompt_instructs_genuine_help(self) -> None:
        client = _make_client("Reply text.")
        draft_reply(_make_content(), _make_config(), client)

        call_args = client.complete.call_args  # type: ignore[union-attr]
        system_prompt = call_args.kwargs["system"]
        assert "help" in system_prompt.lower()

    def test_system_prompt_instructs_natural_mention(self) -> None:
        client = _make_client("Reply text.")
        draft_reply(_make_content(), _make_config(), client)

        call_args = client.complete.call_args  # type: ignore[union-attr]
        system_prompt = call_args.kwargs["system"]
        assert "natural" in system_prompt.lower()

    def test_system_prompt_instructs_no_repetition(self) -> None:
        client = _make_client("Reply text.")
        draft_reply(_make_content(), _make_config(), client)

        call_args = client.complete.call_args  # type: ignore[union-attr]
        system_prompt = call_args.kwargs["system"]
        assert "repeat" in system_prompt.lower()
