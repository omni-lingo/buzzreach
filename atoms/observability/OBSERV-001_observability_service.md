# ATOM: OBSERV-001 — Observability service (metrics & instrumentation)

**Layer:** L2
**Module:** observability
**Effort:** M
**Depends on:** CORE-005, PIPE-001, AI-001

## Inputs (what this atom reads/consumes)
- `src/backend/models/metric.py` — `Metric`
- `src/backend/db/session.py` — session
- BUZZREACH.md — user cares about: opportunities found, AI cost, delivery success

## Outputs (what this atom produces)
- `src/backend/services/observability/__init__.py`
- `src/backend/services/observability/metrics.py` — `MetricsRecorder(session)`. Methods:
  - `record(metric_name: str, value: float, niche: str) -> None` (writes to Metric table; non-fatal if DB fails)
  - `record_search_run(niche: str, candidates_found: int, queries_run: int) -> None`
  - `record_ai_tokens(niche: str, model: str, input_tokens: int, output_tokens: int, cost_usd: float) -> None`
  - `record_delivery(niche: str, opportunities_sent: int, success: bool) -> None`
  - `get_daily_stats(niche: str | None = None) -> dict` (aggregates today's metrics by niche)
- `contracts/observability/metrics.py` — `MetricsData` DTO (for API responses)
- `tests/test_metrics.py` — record metrics, query daily stats, DB failure doesn't crash

## Acceptance criteria
- [ ] All `record_*` calls write to Metric table (parameterized, gate 8)
- [ ] DB failures are logged but do not raise (metric failures ≠ operation failure)
- [ ] `get_daily_stats` aggregates sum/count/avg of metrics by niche
- [ ] Metrics recorded: searches run, candidates found, AI tokens (per model), cost, delivery count
- [ ] `test_metrics.py` passes

## Cross-module contracts
- PIPE-001 calls `metrics.record_search_run(niche, found, queries)` after discovery
- AI-002/003 call `metrics.record_ai_tokens(niche, model, in_tokens, out_tokens, cost)`
- DELIV-002 calls `metrics.record_delivery(niche, count, success)` after sending
- DASH-001 calls `metrics.get_daily_stats()` to display results
- `contracts/observability/metrics.py` imported by dashboard
