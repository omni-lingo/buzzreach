"""Search provider client (DISC-002).

Executes search queries against the configured provider (Google via
SerpAPI) and maps raw results to ``Candidate`` contract objects.
Rate-limited via the injected ``RateLimiter``.
"""

import logging
from typing import Any
from urllib.parse import urlparse

import httpx

from contracts.discovery.candidate import Candidate
from contracts.discovery.search_query import SearchQuery
from src.backend.errors import AppError
from src.backend.services.auth.rate_limiter import RateLimiter
from src.backend.settings import Settings

log = logging.getLogger("buzzreach")

_SERPAPI_BASE_URL = "https://serpapi.com/search"
_MAX_RETRIES = 3
_BACKOFF_BASE_SECONDS = 0.5


class SearchClient:
    """HTTP client for search provider queries.

    Checks the rate limiter before every request (fast-fail, no retry).
    Retries with exponential backoff on provider hard failures.

    Args:
        settings: Application settings with search_api_key and
            search_provider.
        rate_limiter: Injected rate limiter for search quota.
        transport: Optional httpx transport override for testing.
    """

    def __init__(
        self,
        settings: Settings,
        rate_limiter: RateLimiter,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._api_key = settings.search_api_key
        self._rate_limiter = rate_limiter
        self._transport = transport

    def search(self, query: SearchQuery) -> list[Candidate]:
        """Execute a search query and return mapped candidates.

        Args:
            query: Search query with text and freshness params.

        Returns:
            List of Candidate objects from the provider response.

        Raises:
            AppError: ``RATE_LIMITED`` if quota exhausted, or
                ``SEARCH_PROVIDER_ERROR`` on provider failure.
        """
        self._check_rate_limit()
        raw = self._execute_with_retry(query)
        return _parse_candidates(raw)

    def _check_rate_limit(self) -> None:
        """Fast-fail if search quota is exhausted."""
        if not self._rate_limiter.check("search_provider"):
            log.info("Search rate limit exceeded")
            raise AppError(
                code="RATE_LIMITED",
                message="Search provider quota exhausted",
            )

    def _execute_with_retry(
        self, query: SearchQuery
    ) -> dict[str, Any]:
        """Send the HTTP request with exponential backoff on failure."""
        params = _build_params(query, self._api_key)
        last_error: Exception | None = None

        for attempt in range(_MAX_RETRIES):
            try:
                return self._send_request(params)
            except AppError:
                raise
            except Exception as exc:
                last_error = exc
                log.warning(
                    "Search provider attempt failed",
                    extra={
                        "attempt": attempt + 1,
                        "error": str(exc),
                    },
                )
                _backoff(attempt)

        log.error(
            "Search provider exhausted retries",
            extra={"error": str(last_error)},
        )
        raise AppError(
            code="SEARCH_PROVIDER_ERROR",
            message="Search provider failed after retries",
        )

    def _send_request(
        self, params: dict[str, str]
    ) -> dict[str, Any]:
        """Execute a single HTTP request to the search provider."""
        client_kwargs: dict[str, Any] = {}
        if self._transport is not None:
            client_kwargs["transport"] = self._transport

        with httpx.Client(**client_kwargs) as client:
            response = client.get(
                _SERPAPI_BASE_URL, params=params
            )
            if response.status_code >= 400:
                raise AppError(
                    code="SEARCH_PROVIDER_ERROR",
                    message=f"Provider returned HTTP {response.status_code}",
                )
            return response.json()


def _build_params(
    query: SearchQuery, api_key: str
) -> dict[str, str]:
    """Build query parameters for the SerpAPI request."""
    return {
        "q": query.query_text,
        "tbs": query.tbs_param,
        "api_key": api_key,
        "engine": "google",
    }


def _parse_candidates(
    raw: dict[str, Any],
) -> list[Candidate]:
    """Map raw provider JSON to Candidate contract objects."""
    organic = raw.get("organic_results", [])
    return [_map_result(item) for item in organic]


def _map_result(item: dict[str, Any]) -> Candidate:
    """Map a single organic result to a Candidate."""
    url = item.get("link", "")
    return Candidate(
        url=url,
        title=item.get("title", ""),
        snippet=item.get("snippet", ""),
        source=urlparse(url).netloc,
    )


def _backoff(attempt: int) -> None:
    """Sleep with exponential backoff."""
    import time

    delay = _BACKOFF_BASE_SECONDS * (2**attempt)
    time.sleep(delay)
