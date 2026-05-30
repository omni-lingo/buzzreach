# ATOM: RATE-001 — Rate limiter (token bucket, in-memory)

**Layer:** L2
**Module:** auth
**Effort:** M
**Depends on:** INFRA-001

## Inputs (what this atom reads/consumes)
- `src/backend/settings.py` — rate limit config (tokens per minute, burst size)

## Outputs (what this atom produces)
- `src/backend/services/auth/rate_limiter.py` — `RateLimiter` (in-memory token bucket). Methods:
  - `check(key: str, tokens_needed: int = 1) -> bool` (returns True if allowed, False if rate-limited; key can be IP, user_id, or search provider)
  - `reset(key: str) -> None` (for testing)
  - Token bucket refills at configured rate (e.g., 100 tokens/minute)
- `tests/test_rate_limiter.py` — request allowed until quota exhausted, then denied; bucket refills over time (mock time in test)

## Acceptance criteria
- [ ] Pure in-memory implementation (no Redis for MVP)
- [ ] Token bucket algorithm: refill rate configurable, no concurrency issues (use threading.Lock if needed)
- [ ] `check()` returns bool, never raises
- [ ] Keys are strings (IP, user_id, provider name)
- [ ] `test_rate_limiter.py` passes

## Cross-module contracts
- DISC-002 (search client) calls `rate_limiter.check('search_provider')` before each query
- API-001 calls `rate_limiter.check(request.client.host)` for API endpoint rate limits
- No contract exported — service is internal, rate limits are not user-facing APIs
