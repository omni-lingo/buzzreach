# ATOM: CORE-002 — SeenUrl model (own-actions dedup table)

**Layer:** L1
**Module:** core
**Effort:** S
**Depends on:** CORE-001

## Inputs (what this atom reads/consumes)
- `src/backend/db/base.py` — `Base`
- BUZZREACH.md AD-4 — "cache our own actions, never cache the web": columns `url | niche | angle_covered | shown_to | timestamp`

## Outputs (what this atom produces)
- `src/backend/models/__init__.py`
- `src/backend/models/seen_url.py` — `SeenUrl` model, `__tablename__ = "seen_urls"`, `__table_args__ = ({"schema": "buzzreach"},)` plus a unique index on `(url, niche)`. Columns: `id`, `url`, `niche`, `angle_covered` (text, nullable), `shown_to` (text, nullable), `created_at` (tz-aware, default now)
- `migrations/versions/<rev>_create_seen_urls.py` — Alembic migration
- `tests/test_seen_url_model.py` — insert + unique-constraint enforcement on `(url, niche)`

## Acceptance criteria
- [ ] Schema-qualified to `buzzreach` (BUILD_RULES §2)
- [ ] Unique constraint on `(url, niche)` prevents duplicate rows
- [ ] Migration applies cleanly and `alembic check` passes (gate 14)
- [ ] `test_seen_url_model.py` passes

## Cross-module contracts
- FILT-001 (dedup) and PIPE-001 (records seen) read/write this model. No other module writes it.
