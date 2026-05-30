# ATOM: JOB-001 — Scheduled scan job (cron entrypoint)

**Layer:** L2
**Module:** jobs
**Effort:** M
**Depends on:** PIPE-001, DELIV-001, DELIV-002, CFG-002, AUDIT-002

## Inputs (what this atom reads/consumes)
- `src/backend/services/config_loader.py` — `load_all_configs`
- `src/backend/services/pipeline/runner.py` — `run_pipeline`
- `src/backend/services/delivery/digest.py` — `fetch_new_opportunities`, `build_digest`
- `src/backend/services/delivery/sender.py` — `send_digest`
- `src/backend/services/auth/audit_service.py` — `AuditService` to log scan runs
- `src/backend/services/discovery/search_client.py`, `ai/client.py`, `extraction/extractor.py` — concrete deps to inject
- BUZZREACH.md §7 — scheduled job runs Google searches every few hours, then delivers a digest

## Outputs (what this atom produces)
- `src/backend/jobs/__init__.py`
- `src/backend/jobs/scan.py` — `run_scan() -> ScanReport`. For each product config: builds the concrete dependency bundle (including `AuditService`, `MetricsRecorder`), runs `run_pipeline` (which records metrics), accumulates new opportunities, then builds + sends one digest. After digest sends, logs `'scan_completed'` action to audit table (summary: niche, candidates found, drafted, delivered). Structured logging of counts per niche. CLI-invokable: `python -m src.backend.jobs.scan` (the cron target, run every 2 hours).
- `src/backend/jobs/health_check.py` — alias/wrapper: calls `MONITOR-001.run_health_check()`. CLI-invokable: `python -m src.backend.jobs.health_check_job` (run every 1 hour to alert on failures).
- `contracts/jobs/scan_report.py` — `ScanReport` DTO: per-niche candidate/scored/drafted/delivered counts
- `crontab.example` — sample crontab entries: `*/2 * * * * cd /app && python -m src.backend.jobs.scan` (every 2h) and `0 * * * * cd /app && python -m src.backend.jobs.health_check_job` (every 1h)
- `tests/test_scan_job.py` — with pipeline + sender + audit + metrics mocked, `run_scan` iterates all configs, sends one digest per, audits + records metrics; report counts are correct

## Acceptance criteria
- [ ] `run_scan` processes every config from `load_all_configs`
- [ ] Builds dependency bundle and injects into `run_pipeline` (no global state)
- [ ] Sends exactly one digest per scan covering all new opportunities
- [ ] `python -m src.backend.jobs.scan` is runnable as a cron target
- [ ] `ScanReport` counts match processed items
- [ ] `test_scan_job.py` passes

## Cross-module contracts
- Top-level orchestrator: depends on pipeline, delivery, config. Produces no contract consumed by others except `ScanReport` (for logs/monitoring).
