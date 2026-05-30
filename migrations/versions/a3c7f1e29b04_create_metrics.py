"""create_metrics

Revision ID: a3c7f1e29b04
Revises: e1b7b89e593e
Create Date: 2026-05-31 20:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3c7f1e29b04"
down_revision: str | Sequence[str] | None = "e1b7b89e593e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "metrics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("metric_name", sa.String(length=150), nullable=False),
        sa.Column("niche", sa.String(length=150), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="buzzreach",
    )
    op.create_index(
        "ix_metrics_name_niche_timestamp",
        "metrics",
        ["metric_name", "niche", "timestamp"],
        schema="buzzreach",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_metrics_name_niche_timestamp",
        table_name="metrics",
        schema="buzzreach",
    )
    op.drop_table("metrics", schema="buzzreach")
