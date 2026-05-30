"""create_audit_logs

Revision ID: e1b7b89e593e
Revises: 30f12cc46a5e
Create Date: 2026-05-31 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1b7b89e593e"
down_revision: str | Sequence[str] | None = "30f12cc46a5e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(length=150), nullable=False),
        sa.Column("resource_type", sa.String(length=150), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("user_id", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="buzzreach",
    )
    op.create_index(
        "ix_audit_logs_created_at_action",
        "audit_logs",
        ["created_at", "action"],
        schema="buzzreach",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_audit_logs_created_at_action",
        table_name="audit_logs",
        schema="buzzreach",
    )
    op.drop_table("audit_logs", schema="buzzreach")
