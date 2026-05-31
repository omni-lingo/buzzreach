"""Tests for the discovery service (DISC-003).

Validates that discover() builds queries, runs them through a stub client,
deduplicates candidates by URL, and gracefully handles rate limiting by
returning partial results.
"""

from unittest.mock import MagicMock

from contracts.config.product_config import ProductConfig
from contracts.discovery.candidate import Candidate
from contracts.discovery.search_query import SearchQuery
from src.backend.errors import AppError
from src.backend.services.discovery.discovery_service import discover


def _config(**overrides: object) -> ProductConfig:
    """Return a minimal ProductConfig with optional overrides."""
    defaults = {
        "slug": "test-product",
        "product_url": "https://example.com",
        "pitch": "A test product",
        "niche": "testing",
        "keywords": ["keyword1", "keyword2"],
        "tone": "helpful",
        "mention": "TestProduct",
        "freshness": "d",
        "max_queries": 5,
    }
    defaults.update(overrides)
    return ProductConfig(**defaults)


def _candidate(url: str, title: str = "Title") -> Candidate:
    """Build a Candidate with the given URL."""
    return Candidate(
        url=url,
        title=title,
        snippet="snippet",
        source="example.com",
    )


def _stub_client(
    results_per_query: list[list[Candidate]],
) -> MagicMock:
    """Return a stub SearchClient whose search() returns successive lists."""
    client = MagicMock()
    client.search = MagicMock(side_effect=results_per_query)
    return client


def _stub_rate_limiter() -> MagicMock:
    """Return a mock rate limiter (not used directly by discover)."""
    return MagicMock()


class TestBasicDiscovery:
    """discover() builds queries and returns candidates."""

    def test_returns_candidates_from_single_query(self) -> None:
        config = _config(keywords=["kw1"], max_queries=1)
        candidates = [_candidate("https://a.com")]
        client = _stub_client([candidates])

        result = discover(config, _stub_rate_limiter(), client=client)

        assert len(result) == 1
        assert result[0].url == "https://a.com"
        assert isinstance(result[0], Candidate)

    def test_returns_candidates_from_multiple_queries(self) -> None:
        config = _config(keywords=["kw1", "kw2"], max_queries=2)
        client = _stub_client([
            [_candidate("https://a.com")],
            [_candidate("https://b.com")],
        ])

        result = discover(config, _stub_rate_limiter(), client=client)

        assert len(result) == 2
        urls = {c.url for c in result}
        assert urls == {"https://a.com", "https://b.com"}

    def test_passes_queries_to_client(self) -> None:
        config = _config(keywords=["kw1"], max_queries=1)
        client = _stub_client([[]])

        discover(config, _stub_rate_limiter(), client=client)

        client.search.assert_called_once()
        query_arg = client.search.call_args[0][0]
        assert isinstance(query_arg, SearchQuery)


class TestDeduplication:
    """In-run URL dedup: same URL from two queries appears once."""

    def test_duplicate_urls_across_queries_deduped(self) -> None:
        config = _config(keywords=["kw1", "kw2"], max_queries=2)
        client = _stub_client([
            [_candidate("https://dup.com"), _candidate("https://a.com")],
            [_candidate("https://dup.com"), _candidate("https://b.com")],
        ])

        result = discover(config, _stub_rate_limiter(), client=client)

        urls = [c.url for c in result]
        assert urls.count("https://dup.com") == 1
        assert len(result) == 3

    def test_first_occurrence_kept_on_dedup(self) -> None:
        config = _config(keywords=["kw1", "kw2"], max_queries=2)
        first = _candidate("https://dup.com", title="First")
        second = _candidate("https://dup.com", title="Second")
        client = _stub_client([[first], [second]])

        result = discover(config, _stub_rate_limiter(), client=client)

        dup = [c for c in result if c.url == "https://dup.com"]
        assert len(dup) == 1
        assert dup[0].title == "First"


class TestRateLimitHandling:
    """Rate limit hit returns partial results (not empty, no crash)."""

    def test_rate_limit_on_second_query_returns_partial(self) -> None:
        config = _config(keywords=["kw1", "kw2", "kw3"], max_queries=3)
        client = _stub_client([
            [_candidate("https://a.com")],
            AppError(code="RATE_LIMITED", message="quota exhausted"),
        ])

        result = discover(config, _stub_rate_limiter(), client=client)

        assert len(result) == 1
        assert result[0].url == "https://a.com"

    def test_rate_limit_on_first_query_returns_empty(self) -> None:
        config = _config(keywords=["kw1", "kw2"], max_queries=2)
        client = _stub_client([
            AppError(code="RATE_LIMITED", message="quota exhausted"),
        ])

        result = discover(config, _stub_rate_limiter(), client=client)

        assert result == []

    def test_rate_limit_stops_subsequent_queries(self) -> None:
        """After rate limit, remaining queries are NOT attempted."""
        config = _config(keywords=["kw1", "kw2", "kw3"], max_queries=3)
        client = _stub_client([
            [_candidate("https://a.com")],
            AppError(code="RATE_LIMITED", message="quota exhausted"),
        ])

        discover(config, _stub_rate_limiter(), client=client)

        assert client.search.call_count == 2


class TestClientInjection:
    """Client and rate_limiter are injectable for testing."""

    def test_injected_client_used(self) -> None:
        config = _config(keywords=["kw1"], max_queries=1)
        client = _stub_client([[_candidate("https://injected.com")]])

        result = discover(config, _stub_rate_limiter(), client=client)

        assert result[0].url == "https://injected.com"

    def test_all_results_are_candidate_type(self) -> None:
        config = _config(keywords=["kw1", "kw2"], max_queries=2)
        client = _stub_client([
            [_candidate("https://a.com")],
            [_candidate("https://b.com")],
        ])

        result = discover(config, _stub_rate_limiter(), client=client)

        assert all(isinstance(c, Candidate) for c in result)
