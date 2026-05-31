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
        return httpx.Response(status_code=status_code, json=response_body)

    return httpx.MockTransport(handler)


def _rate_limiter(allowed: bool = True) -> MagicMock:
    """Return a mock rate limiter that allows or denies."""
    mock = MagicMock()
    mock.check.return_value = allowed
    return mock


def _make_client(
    transport: httpx.BaseTransport,
    rate_limiter: MagicMock | None = None,
    **settings_overrides: Any,
) -> SearchClient:
    """Build a SearchClient with mock transport and optional overrides."""
    return SearchClient(
        settings=_settings(**settings_overrides),
        rate_limiter=rate_limiter or _rate_limiter(),
        transport=transport,
    )


def _capturing_transport() -> tuple[httpx.MockTransport, list[httpx.Request]]:
    """Return a transport that records requests and an empty response."""
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json=_serpapi_response([]))

    return httpx.MockTransport(handler), captured


class TestCandidateMapping:
    """Provider response maps correctly to Candidate list."""

    def test_maps_organic_results_to_candidates(self) -> None:
        transport = _make_transport(
            _serpapi_response([
                {"link": "https://www.reddit.com/r/tax/post1",
                 "title": "IRS penalty help", "snippet": "CP14 notice"},
                {"link": "https://quora.com/question/abc",
                 "title": "Tax question", "snippet": "How do I appeal?"},
            ])
        )
        results = _make_client(transport).search(_query())

        assert len(results) == 2
        assert all(isinstance(c, Candidate) for c in results)

    def test_candidate_fields_populated(self) -> None:
        transport = _make_transport(
            _serpapi_response([
                {"link": "https://www.reddit.com/r/tax/post1",
                 "title": "IRS penalty help", "snippet": "CP14 notice"},
            ])
        )
        results = _make_client(transport).search(_query())

        assert results[0].url == "https://www.reddit.com/r/tax/post1"
        assert results[0].title == "IRS penalty help"
        assert results[0].snippet == "CP14 notice"
        assert results[0].source == "www.reddit.com"
        assert isinstance(results[0].found_at, datetime)

    def test_empty_results_returns_empty_list(self) -> None:
        transport = _make_transport(_serpapi_response([]))
        assert _make_client(transport).search(_query()) == []


class TestFreshnessParam:
    """tbs freshness param is forwarded to the provider request."""

    @pytest.mark.parametrize("tbs", ["qdr:h", "qdr:w"])
    def test_tbs_param_sent_to_provider(self, tbs: str) -> None:
        transport, captured = _capturing_transport()
        _make_client(transport).search(_query(tbs_param=tbs))

        assert len(captured) == 1
        url = str(captured[0].url)
        encoded = tbs.replace(":", "%3A")
        assert tbs in url or encoded in url


class TestRateLimiter:
    """Rate limiter is consulted before every query."""

    def test_allowed_query_proceeds(self) -> None:
        rl = _rate_limiter(allowed=True)
        transport = _make_transport(_serpapi_response([]))
        _make_client(transport, rate_limiter=rl).search(_query())
        rl.check.assert_called_once_with("search_provider")

    def test_denied_query_raises_rate_limited(self) -> None:
        rl = _rate_limiter(allowed=False)
        transport = _make_transport(_serpapi_response([]))

        with pytest.raises(AppError) as exc_info:
            _make_client(transport, rate_limiter=rl).search(_query())

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

        with pytest.raises(AppError):
            _make_client(transport, rate_limiter=rl).search(_query())

        assert not http_called


class TestProviderErrors:
    """Provider failures surface as AppError(code='SEARCH_PROVIDER_ERROR')."""

    @pytest.mark.parametrize("status", [401, 500])
    def test_http_error_raises_provider_error(self, status: int) -> None:
        transport = _make_transport({"error": "fail"}, status_code=status)

        with pytest.raises(AppError) as exc_info:
            _make_client(transport).search(_query())

        assert exc_info.value.code == "SEARCH_PROVIDER_ERROR"

    def test_connection_error_raises_provider_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused")

        transport = httpx.MockTransport(handler)

        with pytest.raises(AppError) as exc_info:
            _make_client(transport).search(_query())

        assert exc_info.value.code == "SEARCH_PROVIDER_ERROR"


class TestQueryParamSecurity:
    """Query params are passed safely (no secret in URL path)."""

    def test_api_key_sent_as_query_param(self) -> None:
        transport, captured = _capturing_transport()
        _make_client(
            transport, search_api_key="secret-key-xyz"
        ).search(_query())

        url = str(captured[0].url)
        assert "secret-key-xyz" in url
        assert "/secret-key-xyz" not in url
