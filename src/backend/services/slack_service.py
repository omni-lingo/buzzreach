"""Slack bot integration service (EXT-002).

Formats opportunities as Slack Block Kit messages and sends them via
the Slack Web API. Provides both single-opportunity and digest message
formatting with action buttons.
"""

import json
import logging
from typing import Any
from urllib.request import Request, urlopen

from contracts.extensions.slack import SlackMessage
from contracts.opportunity.opportunity import OpportunityData
from src.backend.errors import AppError

log = logging.getLogger("buzzreach.slack")

_SLACK_POST_URL = "https://slack.com/api/chat.postMessage"


def format_opportunity_blocks(
    opp: OpportunityData,
) -> list[dict[str, Any]]:
    """Build Slack Block Kit blocks for a single opportunity.

    Includes: title with link, platform badge, star rating,
    draft reply, and Copy & Open / Dismiss action buttons.
    """
    stars = _relevance_stars(opp.relevance_score)
    opp_id = str(opp.id)

    return [
        _section_block(
            f"*<{opp.url}|{opp.title}>*\n"
            f"`{opp.source.upper()}` | {stars}"
        ),
        _section_block(f">{opp.draft_reply}"),
        _actions_block(opp_id, opp.url),
        {"type": "divider"},
    ]


def format_opportunity_message(
    opp: OpportunityData,
    channel: str,
) -> SlackMessage:
    """Build a complete SlackMessage for a single opportunity."""
    blocks = format_opportunity_blocks(opp)
    return SlackMessage(
        channel=channel,
        blocks=blocks,
        text=f"New opportunity: {opp.title}",
    )


def format_digest_message(
    opportunities: list[OpportunityData],
    channel: str,
) -> SlackMessage:
    """Build a digest SlackMessage for multiple opportunities."""
    if not opportunities:
        return SlackMessage(
            channel=channel,
            blocks=[_section_block("No new opportunities found.")],
            text="BuzzReach Digest: No new opportunities",
        )

    count = len(opportunities)
    header: dict[str, Any] = {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": f"BuzzReach Digest \u2014 {count} opportunities",
        },
    }

    blocks: list[dict[str, Any]] = [header]
    for opp in opportunities:
        blocks.extend(format_opportunity_blocks(opp))

    return SlackMessage(
        channel=channel,
        blocks=blocks,
        text=f"BuzzReach Digest: {count} new opportunities",
    )


def send_opportunity_to_slack(
    opportunity: OpportunityData,
    channel: str,
    bot_token: str,
) -> None:
    """Post a formatted opportunity message to a Slack channel.

    Args:
        opportunity: The opportunity to send.
        channel: Slack channel ID.
        bot_token: Slack bot OAuth token.

    Raises:
        AppError: If the Slack API returns an error response.
    """
    msg = format_opportunity_message(opportunity, channel)
    result = _post_to_slack(payload=msg.model_dump(), token=bot_token)
    _check_slack_response(result)

    log.info(
        "Opportunity sent to Slack",
        extra={
            "opportunity_id": str(opportunity.id),
            "channel": channel,
        },
    )


def send_digest_to_slack(
    opportunities: list[OpportunityData],
    channel: str,
    bot_token: str,
) -> None:
    """Post a digest of opportunities to a Slack channel.

    Skips sending if the opportunity list is empty.
    """
    if not opportunities:
        return

    msg = format_digest_message(opportunities, channel)
    result = _post_to_slack(payload=msg.model_dump(), token=bot_token)
    _check_slack_response(result)

    log.info(
        "Digest sent to Slack",
        extra={
            "count": len(opportunities),
            "channel": channel,
        },
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _relevance_stars(score: float) -> str:
    """Convert a 0.0-1.0 score to a 5-star visual."""
    filled = round(score * 5)
    return "\u2605" * filled + "\u2606" * (5 - filled)


def _section_block(text: str) -> dict[str, Any]:
    """Build a Slack section block with markdown text."""
    return {
        "type": "section",
        "text": {"type": "mrkdwn", "text": text},
    }


def _actions_block(
    opp_id: str, url: str,
) -> dict[str, Any]:
    """Build an actions block with Copy & Open and Dismiss buttons."""
    return {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Copy & Open"},
                "url": url,
                "action_id": f"copy_open_{opp_id}",
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Dismiss"},
                "action_id": f"dismiss_{opp_id}",
                "value": opp_id,
            },
        ],
    }


def _post_to_slack(
    payload: dict[str, Any],
    token: str,
) -> dict[str, Any]:
    """Send a JSON payload to the Slack Web API.

    Returns:
        Parsed JSON response from Slack.
    """
    data = json.dumps(payload).encode()
    req = Request(
        _SLACK_POST_URL,
        data=data,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    with urlopen(req, timeout=10) as resp:  # noqa: S310
        return json.loads(resp.read().decode())


def _check_slack_response(result: dict[str, Any]) -> None:
    """Raise AppError if Slack API returned an error."""
    if not result.get("ok"):
        error = result.get("error", "unknown_error")
        log.error(
            "Slack API error",
            extra={"error_code": "SLACK_API_ERROR", "slack_error": error},
        )
        raise AppError(
            code="SLACK_API_ERROR",
            message=f"Slack API error: {error}",
        )
