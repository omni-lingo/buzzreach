# ATOM: DELIV-002 — Digest sender (email / Slack)

**Layer:** L2
**Module:** delivery
**Effort:** M
**Depends on:** DELIV-001, AUDIT-002, OBSERV-001

## Inputs (what this atom reads/consumes)
- `contracts/delivery/digest.py` — `Digest`
- `src/backend/settings.py` — `smtp_*` and/or `slack_webhook_url`
- `src/backend/services/auth/audit_service.py` — `AuditService` to log digest sends
- `src/backend/services/observability/metrics.py` — `MetricsRecorder` to track delivery success/failure
- BUZZREACH.md §7 — start with email/Slack digest (simplest), phone app later

## Outputs (what this atom produces)
- `src/backend/services/delivery/sender.py` — `send_digest(digest, audit_service, metrics_recorder, session) -> None`. Sends via SMTP and/or Slack webhook depending on configured settings; on success marks the included opportunities `status="delivered"` + `delivered_at`, logs `'digest_sent'` action to audit table, and records `metrics_recorder.record_delivery(niche, count, success=True)`. On failure, raises `AppError(code="DELIVERY_FAILED")`, records `success=False` metric, does not mark delivered or audit.
- `tests/test_sender.py` — SMTP/Slack transport + audit service mocked: successful send marks opportunities delivered and calls audit.log(); failure leaves them `new` and raises coded error (no audit call)

## Acceptance criteria
- [ ] No live SMTP/HTTP in tests — transports mocked; audit_service + metrics_recorder mocked
- [ ] Successful send transitions opportunities `new → delivered` and sets `delivered_at`
- [ ] Successful send calls `audit_service.log('digest_sent', 'digest', count=...)` and `metrics_recorder.record_delivery(..., success=True)`
- [ ] Send failure raises `AppError(code="DELIVERY_FAILED")`, records `success=False` metric, leaves status `new` (no audit call)
- [ ] No secrets in source (gate 9)
- [ ] `test_sender.py` passes

## Cross-module contracts
- JOB-001 calls `send_digest`. Updates `Opportunity` status (CORE-003) — the only writer of the `delivered` transition. Logs to audit table (CORE-004) — the only sender doing so.
