# ATOM: DISC-003 — Discovery service

**Layer:** L2
**Module:** discovery
**Effort:** M
**Depends on:** DISC-001, DISC-002, RATE-001

## Inputs (what this atom reads/consumes)
- `src/backend/services/discovery/query_builder.py` — `build_queries`
- `src/backend/services/discovery/search_client.py` — `SearchClient`, `Candidate`
- `src/backend/services/auth/rate_limiter.py` — injected to `SearchClient`
- `contracts/config/product_config.py` — `ProductConfig`

## Outputs (what this atom produces)
- `src/backend/services/discovery/discovery_service.py` — `discover(config, rate_limiter, client=None) -> list[Candidate]`. Builds queries, creates `SearchClient(rate_limiter)` if client not provided (for injection in tests), runs each query through the client (which rate-limits), flattens + de-duplicates candidates by URL within the run, returns the merged list. If any query hits rate limit, stops early (logs and returns partial results, does not crash).
- `tests/test_discovery_service.py` — given a stub client + stub rate limiter, a multi-keyword config yields deduped candidates across queries; rate limit hit returns partial results (not empty)

## Acceptance criteria
- [ ] In-run URL dedup (same URL from two queries appears once)
- [ ] Client and rate_limiter are injected (testable without network)
- [ ] Returns `Candidate` objects only
- [ ] If rate limiter denies a query, service logs and returns partial results (no crash)
- [ ] `test_discovery_service.py` passes

## Cross-module contracts
- PIPE-001 calls `discover()` with injected rate_limiter as stage 1 of the pipeline. Consumes the `Candidate` contract from DISC-002 and rate limit behavior.
