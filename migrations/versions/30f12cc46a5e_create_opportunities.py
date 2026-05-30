"""create_opportunities

Revision ID: 30f12cc46a5e
Revises: 449772b3cade
Create Date: 2026-05-31 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "30f12cc46a5e"
down_revision: str | Sequence[str] | None = "449772b3cade"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "opportunities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("niche", sa.String(length=150), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("why_matched", sa.Text(), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=False),
        sa.Column("draft_reply", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("NEW", "DELIVERED", "ACTED", "SKIPPED", name="opportunitystatus"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="buzzreach",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("opportunities", schema="buzzreach")
