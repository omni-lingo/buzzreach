"""Anthropic SDK wrapper with retry, prompt caching, and coded errors."""

import logging
import time
from typing import Any

import anthropic
from anthropic import Anthropic

# ---------------------------------------------------------------------------
# Model constants — the only place model IDs are defined in the codebase.
# AD-6: Haiku for cheap scoring, Sonnet for expensive drafting.
# ---------------------------------------------------------------------------
HAIKU: str = "claude-haiku-4-5-20251001"
SONNET: str = "claude-sonnet-4-6"

_MAX_RETRIES: int = 3
_RETRY_BASE_SECONDS: float = 1.0

log = logging.getLogger("buzzreach.ai")


class AiProviderError(Exception):
    """Raised when the Anthropic API call fails after retries."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class AiClient:
    """Thin wrapper around the Anthropic SDK.

    Responsibilities:
    - Build the messages request with prompt-caching on the system block.
    - Retry on rate-limit errors with exponential backoff.
    - Surface hard failures as ``AiProviderError(code="AI_PROVIDER_ERROR")``.
    """

    def __init__(self, api_key: str) -> None:
        self._client: Anthropic = Anthropic(api_key=api_key)

    def complete(
        self,
        model: str,
        system: str,
        user: str,
        max_tokens: int,
    ) -> str:
        """Send a single-turn completion and return the text response.

        Args:
            model: Model ID (use ``HAIKU`` or ``SONNET`` constants).
            system: System prompt (cached via prompt caching).
            user: User message content.
            max_tokens: Maximum tokens in the response.

        Returns:
            The text content of the first response block.

        Raises:
            AiProviderError: On hard failure or empty response.
        """
        request = self._build_request(model, system, user, max_tokens)
        response = self._send_with_retry(request)
        return self._parse_response(response)

    def _build_request(
        self,
        model: str,
        system: str,
        user: str,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Build the SDK request dict with prompt caching on system."""
        return {
            "model": model,
            "max_tokens": max_tokens,
            "system": [
                {
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                },
            ],
            "messages": [
                {"role": "user", "content": user},
            ],
        }

    def _send_with_retry(self, request: dict[str, Any]) -> Any:
        """Send request, retrying on rate-limit up to _MAX_RETRIES times."""
        last_err: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                return self._client.messages.create(**request)
            except anthropic.RateLimitError as exc:
                last_err = exc
                if attempt < _MAX_RETRIES:
                    delay = _RETRY_BASE_SECONDS * (2**attempt)
                    log.warning(
                        "Rate limited, retrying",
                        extra={"attempt": attempt + 1, "delay_s": delay},
                    )
                    time.sleep(delay)
            except Exception as exc:
                raise AiProviderError(
                    code="AI_PROVIDER_ERROR",
                    message=str(exc),
                ) from exc

        raise AiProviderError(
            code="AI_PROVIDER_ERROR",
            message=f"Rate limited after {_MAX_RETRIES} retries: {last_err}",
        )

    def _parse_response(self, response: Any) -> str:
        """Extract text from the first content block."""
        if not response.content:
            raise AiProviderError(
                code="AI_PROVIDER_ERROR",
                message="Empty response from Anthropic API",
            )
        return str(response.content[0].text)
