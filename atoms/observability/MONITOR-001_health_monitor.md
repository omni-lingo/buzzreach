# ATOM: MONITOR-001 — Health monitor & alerting

**Layer:** L2
**Module:** observability
**Effort:** M
**Depends on:** JOB-001, AUDIT-002

## Inputs (what this atom reads/consumes)
- `src/backend/models/audit_log.py` — `AuditLog` (to detect scan failures)
- `src/backend/settings.py` — `slack_webhook_url`, `smtp_*` (alert destinations)
- BUZZREACH.md — user needs to know when the automation breaks

## Outputs (what this atom produces)
- `src/backend/services/observability/health_monitor.py` — `HealthMonitor(session, settings)`. Methods:
  - `check_last_scan(niche: str) -> HealthResult` (was scan run in last 3 hours? logs show success?)
  - `check_search_failures(hours: int = 24) -> list[str]` (grep audit log for `code="SEARCH_PROVIDER_ERROR"`)
  - `check_ai_failures(hours: int = 24) -> list[str]` (grep audit log for `code="AI_PROVIDER_ERROR"`)
  - `check_delivery_failures(hours: int = 24) -> list[str]` (grep audit log for `code="DELIVERY_FAILED"`)
  - `send_alert(subject: str, body: str) -> None` (SMTP or Slack; non-fatal if send fails)
- `src/backend/jobs/health_check_job.py` — CLI-callable `run_health_check()`. Checks all niches, compiles alert message, sends if any issues found. CLI-invokable: `python -m src.backend.jobs.health_check_job` (add to crontab to run every 1 hour).
- `tests/test_health_monitor.py` — simulate scan failure, verify alert triggered; send failure doesn't crash

## Acceptance criteria
- [ ] Detects when last scan failed or is overdue (> 3 hours ago)
- [ ] Detects search, AI, or delivery errors from audit log in past 24h
- [ ] Compiles a summary alert (single email/Slack per check cycle, not 5 alerts)
- [ ] Alert send failure is logged but doesn't stop the program
- [ ] `run_health_check()` is runnable as cron job every 1h
- [ ] `test_health_monitor.py` passes

## Cross-module contracts
- Reads `AuditLog` (CORE-004) to detect failures
- Sends via SMTP/Slack (same as DELIV-002)
- No direct product contracts; background job only
