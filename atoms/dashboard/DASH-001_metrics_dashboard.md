# ATOM: DASH-001 — Metrics dashboard (user sees what's working)

**Layer:** L3/L4
**Module:** dashboard
**Effort:** L
**Depends on:** OBSERV-001, CORE-003, AUDIT-002

## Inputs (what this atom reads/consumes)
- `src/backend/models/opportunity.py` + `contracts/opportunity/opportunity.py` — list opportunities
- `src/backend/services/observability/metrics.py` — `MetricsRecorder.get_daily_stats()`
- `src/backend/models/audit_log.py` — to show last scan time, errors (optional detail view)
- BUZZREACH.md — user cares: "what did I find today? any errors?"

## Outputs (what this atom produces)
- `src/backend/api/v1/dashboard.py` — L3 routes:
  - `GET /api/v1/dashboard` (no auth required for MVP, add JWT later) → returns `DashboardResponse`
  - `GET /api/v1/dashboard/stats?niche=...&days=7` → daily metrics for past N days
  - `GET /api/v1/dashboard/errors?hours=24` → recent errors from audit log
- `src/backend/api/v1/schemas.py` — add `DashboardResponse` (today's opportunities, today's metrics, next scan time, error count)
- `src/frontend` (if adding simple HTML dashboard, optional for MVP) or just API
- `tests/test_dashboard_api.py` — calls return aggregated metrics + opportunity list; no errors shows empty list

## Acceptance criteria
- [ ] GET /api/v1/dashboard returns: opportunities_found (today), acted_on, ai_tokens_used, cost_usd, next_scan_time, error_count
- [ ] GET /api/v1/dashboard/stats aggregates by niche for requested days
- [ ] GET /api/v1/dashboard/errors lists recent failures (last 24h)
- [ ] All responses use `response_model` (gate 4, Pydantic validation)
- [ ] No auth required for MVP (can add AUTH-002 dependency later)
- [ ] `test_dashboard_api.py` passes
- [ ] Each endpoint ≤ 50 lines (split if needed into `src/backend/api/v1/dashboard_routes.py`)

## Cross-module contracts
- Reads `Metric` table (CORE-005) via `MetricsRecorder`
- Reads `Opportunity` (CORE-003) and `AuditLog` (CORE-004)
- `contracts/observability/metrics.py` imported for response shape
- This is the **user-facing API** for monitoring; shapes are contracts that future mobile app will consume
