"""AuditLog ORM model for the core module (CORE-004).

Immutable compliance table tracking actions performed in the system.
Columns: id (UUID PK), action, resource_type, resource_id, change_summary,
user_id, ip_address, created_at.

Composite index on (created_at, action) for query performance.
Immutability enforced via ORM event listeners — rows cannot be
updated or deleted through SQLAlchemy.
"""

import uuid as _uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Index, String, Text, event
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.db.base import Base


class AuditLog(Base):
    """Immutable record of an action taken in the system."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_created_at_action", "created_at", "action"),
        {"schema": "buzzreach"},
    )

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True,
        default=_uuid.uuid4,
    )
    action: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    resource_type: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    resource_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )
    change_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )
    user_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )


def _block_update(mapper: object, connection: object, target: AuditLog) -> None:
    """Prevent UPDATE on AuditLog rows."""
    msg = "AuditLog rows are immutable — UPDATE is not allowed"
    raise RuntimeError(msg)


def _block_delete(mapper: object, connection: object, target: AuditLog) -> None:
    """Prevent DELETE on AuditLog rows."""
    msg = "AuditLog rows are immutable — DELETE is not allowed"
    raise RuntimeError(msg)


event.listen(AuditLog, "before_update", _block_update)
event.listen(AuditLog, "before_delete", _block_delete)
