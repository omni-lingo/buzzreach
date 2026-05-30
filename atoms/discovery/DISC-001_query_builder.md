# ATOM: DISC-001 — Search query builder

**Layer:** L2
**Module:** discovery
**Effort:** S
**Depends on:** CFG-001

## Inputs (what this atom reads/consumes)
- `contracts/config/product_config.py` — `keywords`, `freshness`, `max_queries`
- BUZZREACH.md AD-1 — Google time filters (`tbs=qdr:h|d|w`) return only fresh threads

## Outputs (what this atom produces)
- `src/backend/services/discovery/__init__.py`
- `src/backend/services/discovery/query_builder.py` — `build_queries(config) -> list[SearchQuery]`. Expands keywords into Google queries (optionally `site:reddit.com OR ...` style intent terms), attaches the `tbs=qdr:` freshness param derived from `config.freshness`, caps at `config.max_queries`.
- `contracts/discovery/search_query.py` — `SearchQuery` (query text, tbs param, source_hint)
- `tests/test_query_builder.py` — freshness maps to correct `qdr` code; query count capped at `max_queries`

## Acceptance criteria
- [ ] `freshness` `h|d|w` → `qdr:h|qdr:d|qdr:w`
- [ ] Number of produced queries ≤ `max_queries`
- [ ] Pure function, no network calls, deterministic for a given config
- [ ] `test_query_builder.py` passes

## Cross-module contracts
- DISC-003 consumes `SearchQuery` and passes it to DISC-002's client.
- `contracts/discovery/search_query.py` is the boundary between query construction and the search client.
