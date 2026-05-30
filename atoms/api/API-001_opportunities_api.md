# ATOM: API-001 — Opportunities API

**Layer:** L3
**Module:** api
**Effort:** L
**Depends on:** CORE-003, AUTH-002, RATE-001, AUDIT-002

## Inputs (what this atom reads/consumes)
- `src/backend/models/opportunity.py` + `contracts/opportunity/opportunity.py`
- `src/backend/models/user.py` + `contracts/auth/user.py`
- `src/backend/db/session.py` — session dependency
- `src/backend/services/auth/jwt_service.py` — JWT verify (FastAPI Depends)
- `src/backend/services/auth/rate_limiter.py` — rate limit on endpoints
- `src/backend/services/auth/audit_service.py` — log user actions (act/skip/list)
- BUZZREACH.md §7 / AD-2 — human reviews and acts; app marks acted/skipped

## Outputs (what this atom produces)
- `src/backend/api/__init__.py`
- `src/backend/api/auth_deps.py` — `get_current_user` FastAPI dependency (validates JWT bearer token, returns `UserData`; raises 401 on invalid/missing token)
- `src/backend/api/rate_limit_middleware.py` — middleware to rate-limit by IP (via RATE-001)
- `src/backend/api/main.py` — FastAPI app factory; CORS restricted to explicit origins (no `["*"]`, gate 7); routers mounted under `/api/v1`; middleware added
- `src/backend/api/v1/opportunities.py` — `GET /api/v1/opportunities` (filter by `niche`, `status`, requires JWT), `POST /api/v1/opportunities/{id}/act`, `POST /api/v1/opportunities/{id}/skip` (both require JWT, audit-logged). All responses use `response_model=OpportunityResponse` (Pydantic).
- `src/backend/api/v1/schemas.py` — `OpportunityResponse` (wraps `OpportunityData`)
- `tests/test_opportunities_api.py` — list requires valid JWT (401 without token), act/skip log to audit table, rate limit kicks in after N requests from same IP, unknown id → 404 with error code

## Acceptance criteria
- [ ] All endpoints under `/api/v1/` (naming convention)
- [ ] CORS uses explicit allow-list, never `["*"]` (gate 7)
- [ ] GET/POST endpoints require JWT bearer token (401 if missing/invalid)
- [ ] act/skip actions audit-logged with user_id and IP
- [ ] `response_model` set on every endpoint; generic coded errors to client (no stack traces)
- [ ] Rate limit kicks in after quota (test should verify 429 response)
- [ ] `test_opportunities_api.py` passes; file ≤ 300 lines (split routers if needed)

## Cross-module contracts
- Reads/writes `Opportunity` (CORE-003) via `OpportunityData` and `User` (AUTH-001) via `UserData`
- Uses `JwtService.verify_token()` and `AuditService.log()`
- This is the surface a future mobile/web client (out of MVP scope) will consume — keep `OpportunityResponse` stable
- All action endpoint names and request/response shapes are stable contracts
