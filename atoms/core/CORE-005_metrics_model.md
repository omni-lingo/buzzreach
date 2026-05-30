# ATOM: CORE-005 — Metrics model (product health tracking)

**Layer:** L1
**Module:** core
**Effort:** S
**Depends on:** CORE-001

## Inputs (what this atom reads/consumes)
- `src/backend/db/base.py` — `Base`
- BUZZREACH.md — user needs to know "is this working?"

## Outputs (what this atom produces)
- `src/backend/models/metric.py` — `Metric` model, `__tablename__ = "metrics"`, `__table_args__ = ({"schema": "buzzreach"},)`. Columns: `id`, `metric_name` (str, e.g. "opportunities_found", "ai_tokens_used", "delivery_sent"), `niche` (str), `value` (float), `timestamp` (tz-aware, default now). Index on `(metric_name, niche, timestamp)` for fast aggregation.
- `migrations/versions/<rev>_create_metrics.py` — Alembic migration
- `tests/test_metric_model.py` — insert a metric row; query by name/niche/time range

## Acceptance criteria
- [ ] Schema-qualified to `buzzreach`
- [ ] `metric_name` + `niche` + `timestamp` tuple is queryable (no unique constraint, allows many values per name/niche)
- [ ] Index exists for fast time-range queries (gate 5)
- [ ] Migration + `alembic check` pass (gate 14)
- [ ] `test_metric_model.py` passes

## Cross-module contracts
- OBSERV-001 (observability service) writes to this model only
- DASH-001 (dashboard) reads from this model
