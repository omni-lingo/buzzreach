"""Tests for Slack service layer (EXT-002).

Covers: message formatting, sending via mocked HTTP, and security.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from contracts.extensions.slack import SlackMessage
from contracts.opportunity.opportunity import OpportunityData
from src.backend.errors import AppError
from src.backend.services.slack_service import (
    format_digest_message,
    format_opportunity_blocks,
    format_opportunity_message,
    send_digest_to_slack,
    send_opportunity_to_slack,
)


def _make_opportunity_data(**overrides: object) -> OpportunityData:
    """Build an OpportunityData DTO with sensible defaults."""
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "niche": "project-management",
        "url": "https://reddit.com/r/test/1",
        "title": "Best tool for managing projects?",
        "source": "reddit",
        "why_matched": "Mentions project management software",
        "relevance_score": 0.85,
        "draft_reply": "Check out BuzzReach for this.",
        "status": "new",
        "created_at": datetime.now(UTC),
        "delivered_at": None,
    }
    defaults.update(overrides)
    return OpportunityData(**defaults)


class TestFormatOpportunityBlocks:
    """Verify Slack Block Kit formatting for a single opportunity."""

    def test_blocks_contain_title_with_link(self) -> None:
        opp = _make_opportunity_data(
            title="Need a CRM tool",
            url="https://reddit.com/r/crm/123",
        )
        blocks = format_opportunity_blocks(opp)
        title_block = blocks[0]
        assert "Need a CRM tool" in str(title_block)
        assert "https://reddit.com/r/crm/123" in str(title_block)

    def test_blocks_contain_platform_badge(self) -> None:
        opp = _make_opportunity_data(source="quora")
        blocks = format_opportunity_blocks(opp)
        assert "quora" in str(blocks).lower()

    def test_blocks_contain_relevance_score_stars(self) -> None:
        opp = _make_opportunity_data(relevance_score=0.8)
        blocks = format_opportunity_blocks(opp)
        assert "\u2605" in str(blocks)

    def test_blocks_contain_draft_reply(self) -> None:
        opp = _make_opportunity_data(
            draft_reply="Try our product for this use case.",
        )
        blocks = format_opportunity_blocks(opp)
        assert "Try our product" in str(blocks)

    def test_blocks_contain_action_buttons(self) -> None:
        opp = _make_opportunity_data()
        blocks = format_opportunity_blocks(opp)
        block_str = str(blocks)
        assert "Copy & Open" in block_str
        assert "Dismiss" in block_str


class TestFormatOpportunityMessage:
    """Verify full SlackMessage construction."""

    def test_returns_slack_message(self) -> None:
        opp = _make_opportunity_data()
        msg = format_opportunity_message(opp, channel="C123")
        assert isinstance(msg, SlackMessage)
        assert msg.channel == "C123"
        assert len(msg.blocks) > 0

    def test_fallback_text_set(self) -> None:
        opp = _make_opportunity_data(title="Need help")
        msg = format_opportunity_message(opp, channel="C123")
        assert "Need help" in msg.text


class TestFormatDigestMessage:
    """Verify digest formatting for multiple opportunities."""

    def test_digest_includes_all_opportunities(self) -> None:
        opps = [_make_opportunity_data() for _ in range(3)]
        msg = format_digest_message(opps, channel="C456")
        assert isinstance(msg, SlackMessage)
        assert len(msg.blocks) > 3

    def test_empty_digest(self) -> None:
        msg = format_digest_message([], channel="C456")
        assert "no new opportunities" in msg.text.lower()


class TestSendOpportunityToSlack:
    """Verify send_opportunity_to_slack posts to Slack API."""

    @patch("src.backend.services.slack_service._post_to_slack")
    def test_sends_formatted_message(
        self, mock_post: MagicMock,
    ) -> None:
        mock_post.return_value = {"ok": True}
        opp = _make_opportunity_data()
        send_opportunity_to_slack(
            opportunity=opp,
            channel="C123",
            bot_token="xoxb-test",
        )
        mock_post.assert_called_once()
        assert mock_post.call_args[1]["token"] == "xoxb-test"

    @patch("src.backend.services.slack_service._post_to_slack")
    def test_raises_on_slack_api_error(
        self, mock_post: MagicMock,
    ) -> None:
        mock_post.return_value = {
            "ok": False, "error": "channel_not_found",
        }
        opp = _make_opportunity_data()
        with pytest.raises(AppError) as exc_info:
            send_opportunity_to_slack(
                opportunity=opp,
                channel="C_BAD",
                bot_token="xoxb-test",
            )
        assert exc_info.value.code == "SLACK_API_ERROR"


class TestSendDigestToSlack:
    """Verify send_digest_to_slack posts digest message."""

    @patch("src.backend.services.slack_service._post_to_slack")
    def test_sends_digest(self, mock_post: MagicMock) -> None:
        mock_post.return_value = {"ok": True}
        opps = [_make_opportunity_data() for _ in range(5)]
        send_digest_to_slack(
            opportunities=opps,
            channel="C789",
            bot_token="xoxb-test",
        )
        mock_post.assert_called_once()

    @patch("src.backend.services.slack_service._post_to_slack")
    def test_skips_empty_list(self, mock_post: MagicMock) -> None:
        send_digest_to_slack(
            opportunities=[],
            channel="C789",
            bot_token="xoxb-test",
        )
        mock_post.assert_not_called()


class TestNoSecretsLeaked:
    """Ensure no API keys or tokens appear in Slack messages."""

    def test_message_excludes_tokens(self) -> None:
        opp = _make_opportunity_data()
        msg = format_opportunity_message(opp, channel="C123")
        serialized = str(msg.model_dump())
        assert "xoxb" not in serialized
        assert "api_key" not in serialized.lower()
