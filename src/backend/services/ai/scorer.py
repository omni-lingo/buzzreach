"""Haiku relevance scorer for candidate threads (AI-002).

Builds a prompt from the extracted page content + product config,
sends it to Haiku (cheap stage per AD-6), and parses the structured
JSON verdict into a validated ``RelevanceResult``.
"""

import json
import logging
import re

from pydantic import ValidationError

from contracts.config.product_config import ProductConfig
from contracts.extraction.extracted_content import ExtractedContent
from contracts.scoring.relevance import RelevanceResult
from src.backend.errors import AppError
from src.backend.services.ai.client import HAIKU, AiClient

log = logging.getLogger("buzzreach.ai.scorer")

_MAX_TOKENS: int = 512

_SYSTEM_PROMPT: str = """\
You are a relevance scorer for community marketing. You evaluate whether \
a forum thread is a good opportunity for a product to provide a genuinely \
helpful reply.

You MUST respond with ONLY a JSON object (no markdown, no explanation) \
with exactly these fields:

{
  "score": <float 0.0 to 1.0>,
  "is_seeking_help": <boolean>,
  "angle_already_covered": <boolean>,
  "reason": "<one-sentence explanation>"
}

Scoring guidelines:
- score: 0.0 = completely irrelevant, 1.0 = perfect match
- is_seeking_help: true if the post author is asking for help or advice
- angle_already_covered: true if existing comments already mention the \
product's type of solution or cover the same angle
- reason: brief explanation of your verdict\
"""


def score(
    content: ExtractedContent,
    config: ProductConfig,
    client: AiClient,
) -> RelevanceResult:
    """Score a thread's relevance for the given product.

    Args:
        content: Extracted page content (title, body, comments).
        config: Product configuration (pitch, niche, keywords).
        client: AiClient instance for calling Haiku.

    Returns:
        Validated RelevanceResult with score clamped to [0, 1].

    Raises:
        AppError: With code ``AI_BAD_OUTPUT`` if the model returns
            unparseable or invalid JSON.
    """
    user_prompt = _build_user_prompt(content, config)
    raw_response = client.complete(
        model=HAIKU,
        system=_SYSTEM_PROMPT,
        user=user_prompt,
        max_tokens=_MAX_TOKENS,
    )
    return _parse_verdict(raw_response)


def _build_user_prompt(
    content: ExtractedContent,
    config: ProductConfig,
) -> str:
    """Assemble the user message from content and config."""
    comments_block = _format_comments(content.comments)
    return (
        f"## Product\n"
        f"Niche: {config.niche}\n"
        f"Pitch: {config.pitch}\n"
        f"Mention as: {config.mention}\n\n"
        f"## Thread\n"
        f"URL: {content.url}\n"
        f"Title: {content.title}\n\n"
        f"### Post body\n{content.body}\n\n"
        f"### Existing comments\n{comments_block}\n"
    )


def _format_comments(comments: list[str]) -> str:
    """Format the comment list for the prompt."""
    if not comments:
        return "(no comments yet)"
    return "\n---\n".join(
        f"Comment {i + 1}: {c}" for i, c in enumerate(comments)
    )


def _parse_verdict(raw: str) -> RelevanceResult:
    """Parse and validate the model's JSON verdict.

    Strips optional markdown code fences, parses JSON, clamps score,
    and validates via Pydantic.

    Raises:
        AppError: With code ``AI_BAD_OUTPUT`` on any parse/validation failure.
    """
    cleaned = _strip_code_fences(raw)
    data = _parse_json(cleaned)
    data = _clamp_score(data)
    return _validate_result(data)


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences if present."""
    pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def _parse_json(text: str) -> dict[str, object]:
    """Parse JSON string into a dict."""
    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, TypeError) as exc:
        log.warning(
            "AI returned non-JSON output",
            extra={"raw_output": text[:200], "error": str(exc)},
        )
        raise AppError(
            code="AI_BAD_OUTPUT",
            message=f"Failed to parse AI response as JSON: {exc}",
        ) from exc

    if not isinstance(parsed, dict):
        raise AppError(
            code="AI_BAD_OUTPUT",
            message=f"Expected JSON object, got {type(parsed).__name__}",
        )
    return parsed


def _clamp_score(data: dict[str, object]) -> dict[str, object]:
    """Clamp the score field to [0.0, 1.0] if it's numeric."""
    raw_score = data.get("score")
    if isinstance(raw_score, (int, float)):
        data["score"] = max(0.0, min(1.0, float(raw_score)))
    return data


def _validate_result(data: dict[str, object]) -> RelevanceResult:
    """Validate the parsed dict into a RelevanceResult."""
    try:
        return RelevanceResult(**data)
    except ValidationError as exc:
        log.warning(
            "AI output failed validation",
            extra={"data": data, "error": str(exc)},
        )
        raise AppError(
            code="AI_BAD_OUTPUT",
            message=f"AI response failed validation: {exc}",
        ) from exc
