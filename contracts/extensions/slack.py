"""Cross-module contract for Slack integration data (EXT-002).

Consumers: slack_service (formats messages), slack_webhooks (API layer),
delivery/sender (sends via Slack). Changing this file breaks those modules
at import time.
"""

from uuid import UUID

from pydantic import BaseModel, Field


class SlackBlock(BaseModel):
    """A single Slack Block Kit block for message rendering."""

    type: str
    text: dict[str, str] | None = None
    elements: list[dict[str, object]] | None = None
    accessory: dict[str, object] | None = None


class SlackMessage(BaseModel):
    """A fully-formed Slack message with Block Kit blocks."""

    channel: str
    blocks: list[dict[str, object]] = Field(default_factory=list)
    text: str = ""


class SlashCommandPayload(BaseModel):
    """Parsed payload from a Slack slash command invocation."""

    command: str
    text: str = ""
    user_id: str
    user_name: str
    channel_id: str
    team_id: str
    response_url: str
    trigger_id: str


class SlackEventPayload(BaseModel):
    """Parsed payload from a Slack Events API callback."""

    type: str
    event: dict[str, object] | None = None
    challenge: str | None = None
    team_id: str = ""
    event_id: str = ""


class SlackDigestRequest(BaseModel):
    """Request to send a digest to a Slack channel."""

    user_id: UUID
    channel_id: str
    opportunity_ids: list[UUID] = Field(default_factory=list)
