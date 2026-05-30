# ATOM: CORE-001 — Database base, engine & session

**Layer:** L1
**Module:** core
**Effort:** M
**Depends on:** INFRA-001

## Inputs (what this atom reads/consumes)
- `src/backend/settings.py` — `database_url`, `db_schema`
- `product.yaml` — SQLite path + schema-binding note

## Outputs (what this atom produces)
- `src/backend/db/__init__.py`
- `src/backend/db/base.py` — declarative `Base`; metadata configured with the `buzzreach` schema
- `src/backend/db/session.py` — engine factory + `get_session()` context manager / FastAPI dependency. For SQLite: `ATTACH DATABASE` so the `buzzreach` schema resolves; install a `schema_translate_map` so the same schema-qualified models run unchanged on Postgres (BUILD_RULES §2).
- `alembic.ini`, `migrations/env.py`, `migrations/versions/` — Alembic configured against `Base.metadata`
- `tests/test_db_session.py` — opening a session and a trivial schema-qualified `CREATE/SELECT` round-trips on SQLite

## Acceptance criteria
- [ ] `Base` exposes metadata bound to schema `buzzreach`
- [ ] A model declared with `__table_args__ = {"schema": "buzzreach"}` creates and queries successfully on SQLite (via ATTACH/translate map)
- [ ] `alembic check` / `alembic revision --autogenerate` runs without drift errors (gate 14)
- [ ] Parameterized queries only (gate 8); no wildcard imports
- [ ] `test_db_session.py` passes

## Cross-module contracts
- CORE-002, CORE-003, and every model import `Base` from `src/backend/db/base.py`.
- FILT-001, PIPE-001, DELIV-001, API-001 acquire sessions via `src/backend/db/session.py`.
