# ATOM: TEST-001 — End-to-end integration (anti-silo)

**Layer:** L5
**Module:** tests
**Effort:** M
**Depends on:** JOB-001, API-001

## Inputs (what this atom reads/consumes)
- `src/backend/jobs/scan.py` — `run_scan`
- `src/backend/api/v1/opportunities.py` — opportunities endpoints
- `config/example_irs.json`, `config/example_parking.json`
- BUILD_RULES.md §6 — for every producer→consumer pair, one test exercises BOTH sides

## Outputs (what this atom produces)
- `tests/integration/__init__.py`
- `tests/integration/test_scan_to_api.py` — full loop on a temp SQLite DB with ONLY the external boundaries stubbed (search provider, Anthropic SDK, SMTP/Slack): run `run_scan` against the example configs, then assert the same opportunities are returned by `GET /api/v1/opportunities`, and that a second `run_scan` re-discovering the same URLs produces no duplicate opportunities (dedup proven across the producer/consumer boundary).
- `tests/integration/conftest.py` — fixtures: temp DB + migrations applied, fake search/AI/delivery transports, FastAPI `TestClient`

## Acceptance criteria
- [ ] One test runs the producer (scan/pipeline) then checks the consumer (API) sees the data — true anti-silo test
- [ ] Re-running the scan on the same URLs creates zero duplicate opportunities (validates SeenUrl dedup end-to-end)
- [ ] Only true external services are mocked; all internal modules run for real against SQLite
- [ ] `act`/`skip` via the API transitions status and the change is reflected on re-fetch
- [ ] `test_scan_to_api.py` passes; every file ≤ 300 lines

## Cross-module contracts
- Validates every cross-module contract wired by PIPE-001, DELIV-*, JOB-001, and API-001 actually connect at runtime. Leaf — nothing imports from this atom.
