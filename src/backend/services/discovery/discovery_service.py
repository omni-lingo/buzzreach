"""Discovery service (DISC-003).

Orchestrates search query building and execution. Builds queries from
product config, runs each through the search client (rate-limited),
deduplicates candidates by URL, and returns the merged list.

If the rate limiter denies a query mid-run, the service logs the event
and returns whatever candidates were collected so far (no crash).
"""

import logging

from contracts.config.product_config import ProductConfig
from contracts.discovery.candidate import Candidate
from src.backend.errors import AppError
from src.backend.services.auth.rate_limiter import RateLimiter
from src.backend.services.discovery.query_builder import build_queries
from src.backend.services.discovery.search_client import SearchClient

log = logging.getLogger("buzzreach")


def discover(
    config: ProductConfig,
    rate_limiter: RateLimiter,
    client: SearchClient | None = None,
) -> list[Candidate]:
    """Run discovery for a product configuration.

    Builds search queries from the config, executes each through the
    client (which enforces rate limits), and returns deduplicated
    candidates.

    Args:
        config: Product configuration with keywords and search params.
        rate_limiter: Injected rate limiter for search quota enforcement.
        client: Optional search client override (for testing). If None,
                a real client would be created (requires settings).

    Returns:
        Deduplicated list of Candidate objects from all successful queries.
    """
    queries = build_queries(config)
    log.info(
        "Discovery started",
        extra={
            "product": config.slug,
            "query_count": len(queries),
        },
    )

    candidates = _execute_queries(queries, client)
    deduped = _deduplicate_by_url(candidates)

    log.info(
        "Discovery completed",
        extra={
            "product": config.slug,
            "raw_count": len(candidates),
            "deduped_count": len(deduped),
        },
    )
    return deduped


def _execute_queries(
    queries: list,
    client: SearchClient | None,
) -> list[Candidate]:
    """Run each query through the client, stopping on rate limit.

    Collects candidates from each successful query. If a RATE_LIMITED
    error occurs, logs the event and returns partial results without
    attempting remaining queries.
    """
    if client is None:
        log.warning("No search client provided, returning empty results")
        return []

    candidates: list[Candidate] = []
    for idx, query in enumerate(queries):
        try:
            results = client.search(query)
            candidates.extend(results)
        except AppError as err:
            if err.code == "RATE_LIMITED":
                log.info(
                    "Rate limit hit during discovery, returning partial",
                    extra={
                        "queries_completed": idx,
                        "queries_total": len(queries),
                        "candidates_so_far": len(candidates),
                    },
                )
                break
            raise
    return candidates


def _deduplicate_by_url(
    candidates: list[Candidate],
) -> list[Candidate]:
    """Remove duplicate candidates by URL, keeping first occurrence."""
    seen_urls: set[str] = set()
    unique: list[Candidate] = []
    for candidate in candidates:
        if candidate.url not in seen_urls:
            seen_urls.add(candidate.url)
            unique.append(candidate)
    return unique
