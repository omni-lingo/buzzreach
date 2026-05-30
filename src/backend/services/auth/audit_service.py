"""Audit logging service (AUDIT-002).

Writes immutable audit log rows to the AuditLog table. DB insert failures
are logged but never raised — audit failure must not block the operation
that triggered it.
"""

import logging

from sqlalchemy.orm import Session

from src.backend.models.audit_log import AuditLog

log = logging.getLogger("buzzreach")


class AuditService:
    """Synchronous audit logger backed by the AuditLog table."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def log(
        self,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        change_summary: str | None = None,
        user_id: str | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Write one audit log row.

        Args:
            action: What happened (e.g. ``scan_completed``).
            resource_type: Entity kind (e.g. ``scan``).
            resource_id: Optional entity identifier.
            change_summary: Optional human-readable change description.
            user_id: Actor who triggered the action (None for system).
            ip_address: Request origin IP (None for system/background).
        """
        try:
            row = AuditLog(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                change_summary=change_summary,
                user_id=user_id,
                ip_address=ip_address,
            )
            self._session.add(row)
            self._session.flush()
        except Exception:
            self._session.rollback()
            log.error(
                "Failed to write audit log",
                extra={
                    "error_code": "AUDIT_LOG_ERROR",
                    "action": action,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                },
                exc_info=True,
            )
