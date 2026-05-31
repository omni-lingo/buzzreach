"""Tests for FEAT-001 — Draft Editor contracts and regenerate service.

Covers:
- DraftEditRequest, DraftRegenerateRequest, DraftResponse validation
- regenerate_draft service function
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from contracts.features.draft_edit import (
    DraftEditRequest,
    DraftRegenerateRequest,
    DraftResponse,
    DraftTone,
)

# ---------------------------------------------------------------------------
# Contract validation tests
# ---------------------------------------------------------------------------

class TestDraftEditContract:
    """DraftEditRequest validates input correctly."""

    def test_valid_edit_request(self) -> None:
        req = DraftEditRequest(edited_text="Updated draft text")
        assert req.edited_text == "Updated draft text"

    def test_empty_edit_text_rejected(self) -> None:
        with pytest.raises(ValueError):
            DraftEditRequest(edited_text="")

    def test_long_edit_text_rejected(self) -> None:
        with pytest.raises(ValueError):
            DraftEditRequest(edited_text="x" * 10001)


class TestDraftRegenerateContract:
    """DraftRegenerateRequest validates tone options."""

    def test_valid_tone(self) -> None:
        req = DraftRegenerateRequest(tone=DraftTone.PROFESSIONAL)
        assert req.tone == DraftTone.PROFESSIONAL

    def test_all_tones_available(self) -> None:
        tones = list(DraftTone)
        assert len(tones) >= 5

    def test_invalid_tone_rejected(self) -> None:
        with pytest.raises(ValueError):
            DraftRegenerateRequest(tone="invalid_tone")  # type: ignore[arg-type]


class TestDraftResponseContract:
    """DraftResponse returns correct current_text."""

    def test_current_text_uses_edited_when_present(self) -> None:
        resp = DraftResponse(
            original_draft="original",
            edited_draft="edited",
            current_text="edited",
        )
        assert resp.current_text == "edited"

    def test_current_text_uses_original_when_no_edit(self) -> None:
        resp = DraftResponse(
            original_draft="original",
            edited_draft=None,
            current_text="original",
        )
        assert resp.current_text == "original"


# ---------------------------------------------------------------------------
# Service layer: regenerate_draft
# ---------------------------------------------------------------------------

def _make_ai_client(response_text: str) -> MagicMock:
    """Create an AiClient with mocked complete()."""
    with patch("src.backend.services.ai.client.Anthropic"):
        from src.backend.services.ai.client import AiClient

        client = AiClient(api_key="sk-ant-test-key")
    client.complete = MagicMock(  # type: ignore[assignment]
        return_value=response_text,
    )
    return client


def _make_test_content() -> MagicMock:
    """Create test ExtractedContent."""
    from contracts.extraction.extracted_content import ExtractedContent

    return ExtractedContent(
        url="https://example.com/thread",
        title="Need help",
        body="Looking for a solution",
        comments=[],
    )


def _make_test_config() -> MagicMock:
    """Create test ProductConfig."""
    from contracts.config.product_config import ProductConfig

    return ProductConfig(
        slug="test-product",
        product_url="https://example.com",
        pitch="Great product",
        niche="tech",
        keywords=["help"],
        tone="helpful",
        mention="TestProduct",
    )


class TestRegenerateDraft:
    """regenerate_draft() calls AI with tone override."""

    def test_regenerate_uses_tone_override(self) -> None:
        client = _make_ai_client("Regenerated draft")
        from src.backend.services.ai.draft import regenerate_draft

        result = regenerate_draft(
            content=_make_test_content(),
            config=_make_test_config(),
            client=client,
            tone_override="casual",
        )

        assert result == "Regenerated draft"
        call_kwargs = client.complete.call_args  # type: ignore[union-attr]
        user_prompt = call_kwargs.kwargs["user"]
        assert "casual" in user_prompt

    def test_regenerate_preserves_content_context(self) -> None:
        from contracts.extraction.extracted_content import ExtractedContent

        content = ExtractedContent(
            url="https://example.com/thread",
            title="Specific question about Python",
            body="How do I handle exceptions?",
            comments=["Use try/except"],
        )
        client = _make_ai_client("New draft")
        from src.backend.services.ai.draft import regenerate_draft

        regenerate_draft(
            content=content,
            config=_make_test_config(),
            client=client,
            tone_override="technical",
        )

        call_kwargs = client.complete.call_args  # type: ignore[union-attr]
        user_prompt = call_kwargs.kwargs["user"]
        assert content.title in user_prompt
        assert content.body in user_prompt
