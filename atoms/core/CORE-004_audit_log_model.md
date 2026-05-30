# ATOM: CORE-004 — AuditLog model (compliance & security)

**Layer:** L1
**Module:** core
**Effort:** S
**Depends on:** CORE-001

## Inputs (what this atom reads/consumes)
- `src/backend/db/base.py` — `Base`
- `src/backend/models/seen_url.py` — example of schema-qualified model

## Outputs (what this atom produces)
- `src/backend/models/audit_log.py` — `AuditLog` model, `__tablename__ = "audit_logs"`, `__table_args__ = ({"schema": "buzzreach"},)`. Columns: `id`, `action` (str, e.g. "opportunity_acted", "scan_completed"), `resource_type` (str, e.g. "opportunity", "scan"), `resource_id` (str, nullable), `change_summary` (text, nullable), `user_id` (str, nullable), `ip_address` (str, nullable), `created_at` (tz-aware, default now). Index on `(created_at, action)` for query performance.
- `migrations/versions/<rev>_create_audit_logs.py` — Alembic migration
- `tests/test_audit_log_model.py` — insert an audit log row; immutable (no update/delete)

## Acceptance criteria
- [ ] Schema-qualified to `buzzreach`
- [ ] Immutable after creation (no UPDATE/DELETE allowed via ORM)
- [ ] `action` and `resource_type` are required strings (enable filtering)
- [ ] Migration applies cleanly; `alembic check` passes (gate 14)
- [ ] `test_audit_log_model.py` passes

## Cross-module contracts
- AUDIT-002 (audit service) reads/writes this model. No other module writes to it.
- Compliance teams will query this table for forensics.
