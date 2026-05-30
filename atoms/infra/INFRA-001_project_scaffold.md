# ATOM: INFRA-001 — Project scaffold & settings

**Layer:** L1
**Module:** infra
**Effort:** M
**Depends on:** none

## Inputs (what this atom reads/consumes)
- `product.yaml` — tech stack, paths, db type, schema name
- `BUILD_RULES.md` — file/function limits, forbidden patterns, naming

## Outputs (what this atom produces)
- `pyproject.toml` — project metadata + deps (fastapi, sqlalchemy, alembic, pydantic, pydantic-settings, anthropic, httpx, readability-lxml, beautifulsoup4, pytest, ruff, mypy)
- `src/__init__.py`, `src/backend/__init__.py` — make the tree importable (gate 19 does `import src.backend...`)
- `src/backend/settings.py` — `Settings(BaseSettings)`: `database_url`, `db_schema` (default `buzzreach`), `anthropic_api_key`, `search_api_key`, `search_provider`, `smtp_*`/`slack_webhook_url`, `config_dir`. Loaded from env via pydantic-settings.
- `src/backend/logging_config.py` — `setup_logging()` returning a structured (JSON) logger; no `print`
- `tests/__init__.py`, `tests/test_settings.py` — settings load from env with defaults
- `.env.example` — documents every required env var (no real secrets)
- `.gitignore` — ignores `data/`, `state/`, `*.db`, `.env`, `__pycache__`, `logs/`

## Acceptance criteria
- [ ] `python -c "import src.backend.settings"` succeeds
- [ ] `Settings()` reads all values from env; `db_schema` defaults to `buzzreach`
- [ ] No hardcoded secrets — only `.env.example` placeholders (gate 9)
- [ ] `setup_logging()` emits structured logs with `extra={...}` context, never f-string interpolation
- [ ] `test_settings.py` passes
- [ ] Every file ≤ 300 lines, every function ≤ 50 lines

## Cross-module contracts
- Every other atom imports `Settings` from `src/backend/settings.py`.
- Every other atom imports the logger from `src/backend/logging_config.py`.
