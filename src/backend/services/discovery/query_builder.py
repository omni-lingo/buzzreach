"""Search query builder (DISC-001).

Expands product keywords into Google search queries with freshness
parameters. Pure function — no network calls, deterministic output.
"""

from contracts.config.product_config import ProductConfig
from contracts.discovery.search_query import SearchQuery

_INTENT_SITES: list[str] = [
    "site:reddit.com",
    "site:quora.com",
]

_INTENT_SUFFIX: str = " OR ".join(_INTENT_SITES)


def _freshness_to_tbs(freshness: str) -> str:
    """Map config freshness code to Google ``tbs`` parameter value."""
    return f"qdr:{freshness}"


def _build_keyword_query(keyword: str, intent_suffix: str) -> str:
    """Build a single query string from a keyword and intent suffix."""
    return f"{keyword} {intent_suffix}"


def build_queries(config: ProductConfig) -> list[SearchQuery]:
    """Expand product keywords into capped, freshness-tagged queries.

    Args:
        config: Validated product configuration with keywords, freshness,
                and max_queries.

    Returns:
        A list of ``SearchQuery`` objects, length <= ``config.max_queries``.
    """
    tbs = _freshness_to_tbs(config.freshness)
    queries: list[SearchQuery] = []

    for keyword in config.keywords:
        if len(queries) >= config.max_queries:
            break
        query_text = _build_keyword_query(keyword, _INTENT_SUFFIX)
        queries.append(
            SearchQuery(
                query_text=query_text,
                tbs_param=tbs,
                source_hint="reddit",
            )
        )

    return queries
