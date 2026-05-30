# ATOM: DISC-002 — Search provider client

**Layer:** L2
**Module:** discovery
**Effort:** M
**Depends on:** INFRA-001, RATE-001

## Inputs (what this atom reads/consumes)
- `src/backend/settings.py` — `search_provider`, `search_api_key`
- `src/backend/services/auth/rate_limiter.py` — `RateLimiter` to enforce search quota
- BUZZREACH.md AD-1 — Google search (SerpAPI / Google Custom Search), not per-platform scrapers

## Outputs (what this atom produces)
- `src/backend/services/discovery/search_client.py` — `SearchClient(rate_limiter: RateLimiter)` with `search(query: SearchQuery) -> list[Candidate]`. Before each query, calls `rate_limiter.check('search_provider')` and raises `AppError(code="RATE_LIMITED")` if quota exhausted (fast-fail, no retry). Uses `httpx` against the configured provider; passes the `tbs` freshness param; maps raw results to `Candidate`. On provider hard failure, retries with backoff; raises `AppError(code="SEARCH_PROVIDER_ERROR")` on exhaustion.
- `contracts/discovery/candidate.py` — `Candidate` Pydantic model: `url`, `title`, `snippet`, `source` (host), `found_at`
- `tests/test_search_client.py` — provider response (mocked via `httpx` transport / `respx`) maps to `Candidate` list; rate limiter allows/denies queries; error path raises coded error

## Acceptance criteria
- [ ] No live network call in tests — provider HTTP is mocked; rate limiter is mocked
- [ ] `tbs` freshness param is forwarded to the provider request
- [ ] Rate limiter is consulted before every query; `code="RATE_LIMITED"` raised if denied
- [ ] Provider failures surface as `AppError(code="SEARCH_PROVIDER_ERROR")`
- [ ] Parameterized/escaped query params; no secret in source (gate 9)
- [ ] `test_search_client.py` passes

## Cross-module contracts
- DISC-003 calls `SearchClient.search` (injects rate_limiter). PIPE-001 and extraction consume `Candidate`.
- `contracts/discovery/candidate.py` is imported by extraction, filter, and pipeline.
- Rate limiter is injected as a dependency (testable in isolation).
