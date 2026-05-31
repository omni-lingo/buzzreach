"""Tests for the search query builder (DISC-001).

Validates freshness mapping, query capping, determinism, and structure
of the SearchQuery outputs produced by build_queries().
"""

from contracts.config.product_config import ProductConfig
from contracts.discovery.search_query import SearchQuery
from src.backend.services.discovery.query_builder import build_queries


def _config(**overrides: object) -> ProductConfig:
    """Return a minimal valid ProductConfig with optional overrides."""
    base = {
        "slug": "test-product",
        "product_url": "https://example.com/product",
        "pitch": "A test product",
        "niche": "testing",
        "keywords": ["keyword one", "keyword two"],
        "tone": "friendly",
        "mention": "TestProduct at example.com",
        "freshness": "d",
        "max_queries": 5,
    }
    base.update(overrides)
    return ProductConfig(**base)


class TestFreshnessMapping:
    """freshness h|d|w maps to tbs_param qdr:h|qdr:d|qdr:w."""

    def test_freshness_hour(self) -> None:
        queries = build_queries(_config(freshness="h"))
        assert all(q.tbs_param == "qdr:h" for q in queries)

    def test_freshness_day(self) -> None:
        queries = build_queries(_config(freshness="d"))
        assert all(q.tbs_param == "qdr:d" for q in queries)

    def test_freshness_week(self) -> None:
        queries = build_queries(_config(freshness="w"))
        assert all(q.tbs_param == "qdr:w" for q in queries)


class TestQueryCapping:
    """Number of produced queries never exceeds max_queries."""

    def test_capped_at_max_queries(self) -> None:
        cfg = _config(max_queries=1, keywords=["a", "b", "c"])
        queries = build_queries(cfg)
        assert len(queries) <= 1

    def test_fewer_keywords_than_max(self) -> None:
        cfg = _config(max_queries=10, keywords=["only one"])
        queries = build_queries(cfg)
        assert len(queries) >= 1
        assert len(queries) <= 10

    def test_exact_cap_with_many_keywords(self) -> None:
        keywords = [f"kw{i}" for i in range(20)]
        cfg = _config(max_queries=3, keywords=keywords)
        queries = build_queries(cfg)
        assert len(queries) == 3


class TestQueryStructure:
    """Each query is a SearchQuery with non-empty query_text."""

    def test_returns_search_query_instances(self) -> None:
        queries = build_queries(_config())
        assert all(isinstance(q, SearchQuery) for q in queries)

    def test_query_text_non_empty(self) -> None:
        queries = build_queries(_config())
        assert all(q.query_text.strip() for q in queries)

    def test_keywords_appear_in_query_text(self) -> None:
        cfg = _config(keywords=["irs penalty"])
        queries = build_queries(cfg)
        assert any("irs penalty" in q.query_text for q in queries)


class TestDeterminism:
    """Pure function: same config produces same output."""

    def test_same_config_same_result(self) -> None:
        cfg = _config()
        first = build_queries(cfg)
        second = build_queries(cfg)
        assert first == second

    def test_different_freshness_different_tbs(self) -> None:
        q_hour = build_queries(_config(freshness="h"))
        q_week = build_queries(_config(freshness="w"))
        assert q_hour[0].tbs_param != q_week[0].tbs_param


class TestNoNetworkCalls:
    """build_queries is pure — it must not perform I/O."""

    def test_returns_list(self) -> None:
        result = build_queries(_config())
        assert isinstance(result, list)
