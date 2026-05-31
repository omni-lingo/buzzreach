"""Sonnet draft generator for confirmed opportunities (AI-003).

Builds a prompt from extracted page content + product config, sends it
to Sonnet (quality stage per AD-6), and returns the drafted reply text.
The prompt is designed to produce replies that read human, lead with
genuine help, mention the product naturally, and avoid repeating what
existing comments already said.
"""

import logging

from contracts.config.product_config import ProductConfig
from contracts.extraction.extracted_content import ExtractedContent
from src.backend.services.ai.client import SONNET, AiClient

log = logging.getLogger("buzzreach.ai.draft")

_MAX_TOKENS: int = 1024

_SYSTEM_PROMPT: str = """\
You are a community marketing assistant. Your job is to draft a reply \
to a forum thread that is genuinely helpful to the person asking.

Rules you MUST follow:
1. Lead with real, specific help that addresses the person's actual \
problem. The reply must be useful even if the reader ignores the \
product mention.
2. Write in a human, conversational tone matching the style described \
below. Do NOT sound like a corporate press release or a chatbot.
3. Mention the product naturally, as something you've found helpful or \
as one option among several — never as the sole focus or a hard sell.
4. Read the existing comments carefully and do NOT repeat advice, \
suggestions, or angles that have already been covered. Add new value.
5. Keep it concise — aim for 2-4 short paragraphs. No bullet-point \
walls, no numbered lists unless the thread style calls for it.
6. Never use phrases like "I'm an AI", "As an AI", or reveal that \
this reply was generated.\
"""


def draft_reply(
    content: ExtractedContent,
    config: ProductConfig,
    client: AiClient,
) -> str:
    """Draft a helpful reply for a confirmed opportunity.

    Args:
        content: Extracted page content (title, body, comments).
        config: Product configuration (tone, pitch, mention, product_url).
        client: AiClient instance for calling Sonnet.

    Returns:
        The drafted reply text ready for human review.
    """
    user_prompt = _build_user_prompt(content, config)
    return client.complete(
        model=SONNET,
        system=_SYSTEM_PROMPT,
        user=user_prompt,
        max_tokens=_MAX_TOKENS,
    )


def regenerate_draft(
    content: ExtractedContent,
    config: ProductConfig,
    client: AiClient,
    tone_override: str,
) -> str:
    """Regenerate a draft with a different tone, same URL context.

    Args:
        content: Extracted page content (title, body, comments).
        config: Product configuration (tone, pitch, mention, product_url).
        client: AiClient instance for calling Sonnet.
        tone_override: New tone to use instead of config.tone.

    Returns:
        The regenerated reply text.
    """
    user_prompt = _build_user_prompt(content, config, tone_override)
    log.info(
        "Regenerating draft",
        extra={"tone_override": tone_override, "url": content.url},
    )
    return client.complete(
        model=SONNET,
        system=_SYSTEM_PROMPT,
        user=user_prompt,
        max_tokens=_MAX_TOKENS,
    )


def _build_user_prompt(
    content: ExtractedContent,
    config: ProductConfig,
    tone_override: str | None = None,
) -> str:
    """Assemble the user message from content and config."""
    tone = tone_override or config.tone
    comments_block = _format_comments(content.comments)
    return (
        f"## Your tone\n"
        f"{tone}\n\n"
        f"## Product to mention\n"
        f"Name: {config.mention}\n"
        f"URL: {config.product_url}\n"
        f"Pitch: {config.pitch}\n\n"
        f"## Thread to reply to\n"
        f"Title: {content.title}\n\n"
        f"### Original post\n{content.body}\n\n"
        f"### Existing comments (do not repeat these)\n"
        f"{comments_block}\n\n"
        f"## Your task\n"
        f"Write a reply that helps the poster with their problem. "
        f"Mention {config.mention} ({config.product_url}) naturally "
        f"if relevant, but lead with genuine help first."
    )


def _format_comments(comments: list[str]) -> str:
    """Format the comment list for the prompt."""
    if not comments:
        return "(no comments yet)"
    return "\n---\n".join(
        f"Comment {i + 1}: {c}" for i, c in enumerate(comments)
    )
