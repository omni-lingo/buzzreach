"""Tests for the search provider client (DISC-002).

All provider HTTP is mocked via httpx.MockTransport. The rate limiter is
mocked with a simple stub. No live network calls.
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest

from contracts.discovery.candidate import Candidate
from contracts.discovery.search_query import SearchQuery
from src.backend.errors import AppError
from src.backend.services.discovery.search_client import SearchClient
from src.backend.settings import Settings


def _settings(**overrides: Any) -> Settings:
    """Return Settings with search config and optional overrides."""
    defaults: dict[str, Any] = {
        "search_provider": "google",
        "search_api_key": "test-api-key-123",
    }
    defaults.update(overrides)
    return Settings(**defaults)


def _query(
    query_text: str = "irs penalty help site:reddit.com",
    tbs_param: str = "qdr:d",
) -> SearchQuery:
    return SearchQuery(query_text=query_text, tbs_param=tbs_param)


def _serpapi_response(results: list[dict[str, str]]) -> dict[str, Any]:
    """Build a minimal SerpAPI-style response."""
    return {
        "organic_results": [
            {
                "link": r["link"],
                "title": r.get("title", "Test Title"),
                "snippet": r.get("snippet", "Test snippet text"),
            }
            for r in results
        ],
    }


def _make_transport(
    response_body: dict[str, Any],
    status_code: int = 200,
) -> httpx.MockTransport:
    """Build a mock transport returning a fixed JSON response."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=status_code,
            json=response_body,
        )

    return httpx.MockTransport(handler)


def _rate_limiter(allowed: bool = True) -> MagicMock:
    """Return a mock rate limiter that allows or denies."""
    mock = MagicMock()
    mock.check.return_value = allowed
    return mock


class TestCandidateMapping:
    """Provider response maps correctly to Candidate list."""

    def test_maps_organic_results_to_candidates(self) -> None:
        transport = _make_transport(
            _serpapi_response([
                {
                    "link": "https://www.reddit.com/r/tax/post1",
                    "title": "IRS penalty help",
                    "snippet": "I got a CP14 notice",
                },
                {
                    "link": "https://quora.com/question/abc",
                    "title": "Tax question",
                    "snippet": "How do I appeal?",
                },
            ])
        )
        client = SearchClient(
            settings=_settings(),
            rate_limiter=_rate_limiter(),
            transport=transport,
        )

        results = client.search(_query())

        assert len(results) == 2
        assert all(isinstance(c, Candidate) for c in results)

    def test_candidate_fields_populated(self) -> None:
        transport = _make_transport(
            _serpapi_response([
                {
                    "link": "https://www.reddit.com/r/tax/post1",
                    "title": "IRS penalty help",
                    "snippet": "I got a CP14 notice",
                },
            ])
        )
        client = SearchClient(
            settings=_settings(),
            rate_limiter=_rate_limiter(),
            transport=transport,
        )

        results = client.search(_query())

        assert results[0].url == "https://www.reddit.com/r/tax/post1"
        assert results[0].title == "IRS penalty help"
        assert results[0].snippet == "I got a CP14 notice"
        assert results[0].source == "www.reddit.com"
        assert isinstance(results[0].found_at, datetime)

    def test_empty_results_returns_empty_list(self) -> None:
        transport = _make_transport(_serpapi_response([]))
        client = SearchClient(
            settings=_settings(),
            rate_limiter=_rate_limiter(),
            transport=transport,
        )

        results = client.search(_query())

        assert results == []


class TestFreshnessParam:
    """tbs freshness param is forwarded to the provider request."""

    def test_tbs_param_sent_to_provider(self) -> None:
        captured_requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured_requests.append(request)
            return httpx.Response(200, json=_serpapi_response([]))

        transport = httpx.MockTransport(handler)
        client = SearchClient(
            settings=_settings(),
            rate_limiter=_rate_limiter(),
            transport=transport,
        )

        client.search(_query(tbs_param="qdr:h"))

        assert len(captured_requests) == 1
        url = captured_requests[0].url
        assert "tbs=qdr%3Ah" in str(url) or "tbs=qdr:h" in str(url)

    def test_different_tbs_values_forwarded(self) -> None:
        captured_requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured_requests.append(request)
            return httpx.Response(200, json=_serpapi_response([]))

        transport = httpx.MockTransport(handler)
        client = SearchClient(
            settings=_settings(),
            rate_limiter=_rate_limiter(),
            transport=transport,
        )

        client.search(_query(tbs_param="qdr:w"))

        url = captured_requests[0].url
        assert "tbs=qdr%3Aw" in str(url) or "tbs=qdr:w" in str(url)


class TestRateLimiter:
    """Rate limiter is consulted before every query."""

    def test_allowed_query_proceeds(self) -> None:
        rl = _rate_limiter(allowed=True)
        transport = _make_transport(_serpapi_response([]))
        client = SearchClient(
            settings=_settings(),
            rate_limiter=rl,
            transport=transport,
        )

        client.search(_query())

        rl.check.assert_called_once_with("search_provider")

    def test_denied_query_raises_rate_limited(self) -> None:
        rl = _rate_limiter(allowed=False)
        transport = _make_transport(_serpapi_response([]))
        client = SearchClient(
            settings=_settings(),
            rate_limiter=rl,
            transport=transport,
        )

        with pytest.raises(AppError) as exc_info:
            client.search(_query())

        assert exc_info.value.code == "RATE_LIMITED"

    def test_rate_limiter_checked_before_http(self) -> None:
        """If rate limited, no HTTP request should be made."""
        http_called = False

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal http_called
            http_called = True
            return httpx.Response(200, json=_serpapi_response([]))

        transport = httpx.MockTransport(handler)
        rl = _rate_limiter(allowed=False)
        client = SearchClient(
            settings=_settings(),
            rate_limiter=rl,
            transport=transport,
        )

        with pytest.raises(AppError):
            client.search(_query())

        assert not http_called


class TestProviderErrors:
    """Provider failures surface as AppError(code='SEARCH_PROVIDER_ERROR')."""

    def test_http_500_raises_provider_error(self) -> None:
        transport = _make_transport(
            {"error": "internal server error"},
            status_code=500,
        )
        client = SearchClient(
            settings=_settings(),
            rate_limiter=_rate_limiter(),
            transport=transport,
        )

        with pytest.raises(AppError) as exc_info:
            client.search(_query())

        assert exc_info.value.code == "SEARCH_PROVIDER_ERROR"

    def test_http_401_raises_provider_error(self) -> None:
        transport = _make_transport(
            {"error": "unauthorized"},
            status_code=401,
        )
        client = SearchClient(
            settings=_settings(),
            rate_limiter=_rate_limiter(),
            transport=transport,
        )

        with pytest.raises(AppError) as exc_info:
            client.search(_query())

        assert exc_info.value.code == "SEARCH_PROVIDER_ERROR"

    def test_connection_error_raises_provider_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused")

        transport = httpx.MockTransport(handler)
        client = SearchClient(
            settings=_settings(),
            rate_limiter=_rate_limiter(),
            transport=transport,
        )

        with pytest.raises(AppError) as exc_info:
            client.search(_query())

        assert exc_info.value.code == "SEARCH_PROVIDER_ERROR"


class TestQueryParamSecurity:
    """Query params are passed safely (no secret in URL path)."""

    def test_api_key_sent_as_query_param(self) -> None:
        captured_requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured_requests.append(request)
            return httpx.Response(200, json=_serpapi_response([]))

        transport = httpx.MockTransport(handler)
        client = SearchClient(
            settings=_settings(search_api_key="secret-key-xyz"),
            rate_limiter=_rate_limiter(),
            transport=transport,
        )

        client.search(_query())

        url = str(captured_requests[0].url)
        assert "secret-key-xyz" in url
        assert "/secret-key-xyz" not in url
