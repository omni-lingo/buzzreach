# ATOM: AUDIT-002 — Audit logging service

**Layer:** L2
**Module:** auth
**Effort:** M
**Depends on:** CORE-004, AUTH-001

## Inputs (what this atom reads/consumes)
- `src/backend/models/audit_log.py` — `AuditLog`
- `src/backend/db/session.py` — session
- `src/backend/services/auth/jwt_service.py` — to get user context (optional)

## Outputs (what this atom produces)
- `src/backend/services/auth/audit_service.py` — `AuditService(session)`. Method:
  - `log(action, resource_type, resource_id, change_summary, user_id=None, ip_address=None) -> None`
  - Writes to `AuditLog` table; synchronous (no async job); raises `AppError(code="AUDIT_LOG_ERROR")` on DB failure (non-fatal)
- `tests/test_audit_service.py` — log an action, verify row inserted; db failure doesn't crash (logged but exception swallowed with code)

## Acceptance criteria
- [ ] Every call to `log()` writes one row to AuditLog (parameterized insert, gate 8)
- [ ] DB insert failure is logged but does not raise (audit failure ≠ operation failure)
- [ ] `user_id` and `ip_address` are optional (system actions)
- [ ] `test_audit_service.py` passes

## Cross-module contracts
- JOB-001 calls `audit_service.log('scan_completed', 'scan', ...)` after each run
- API-001 calls `audit_service.log('opportunity_acted', 'opportunity', opportunity.id, ...)` after each user action
- PIPE-001 calls `audit_service.log('opportunity_generated', 'opportunity', ...)` per draft
- DELIV-002 calls `audit_service.log('digest_sent', 'digest', ...)` after send
