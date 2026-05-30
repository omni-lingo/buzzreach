# ATOM: CFG-002 — Config loader service

**Layer:** L2
**Module:** config
**Effort:** S
**Depends on:** CFG-001

## Inputs (what this atom reads/consumes)
- `contracts/config/product_config.py` — `ProductConfig`
- `src/backend/settings.py` — `config_dir` (directory of per-product JSON files)

## Outputs (what this atom produces)
- `src/backend/services/__init__.py`
- `src/backend/services/config_loader.py` — `load_config(slug) -> ProductConfig` and `load_all_configs() -> list[ProductConfig]`. Reads `*.json` from `config_dir`, validates each into `ProductConfig`, raises `AppError(code="CONFIG_NOT_FOUND")` / `AppError(code="CONFIG_INVALID")` on failure.
- `src/backend/errors.py` — `AppError(code, message)` base exception (error codes, not bare messages — BUILD_RULES §9)
- `config/example_irs.json`, `config/example_parking.json` — two real example configs (IRS Penalty Calculator, ParkingAppealMate) per the dogfooding plan
- `tests/test_config_loader.py` — loads examples, rejects malformed JSON, raises coded errors

## Acceptance criteria
- [ ] `load_all_configs()` returns every valid config and skips/raises on invalid ones per documented behavior
- [ ] Coded `AppError` raised (never a bare `ValueError`) on missing/invalid config
- [ ] Example configs validate against `ProductConfig`
- [ ] `test_config_loader.py` passes

## Cross-module contracts
- JOB-001 calls `load_all_configs()` to drive each scan cycle.
- `AppError` from `src/backend/errors.py` is the shared exception base imported across services.
