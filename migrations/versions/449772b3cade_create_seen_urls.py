"""create_seen_urls

Revision ID: 449772b3cade
Revises: 285d707285d9
Create Date: 2026-05-31 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "449772b3cade"
down_revision: str | Sequence[str] | None = "285d707285d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "seen_urls",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("niche", sa.String(length=150), nullable=False),
        sa.Column("angle_covered", sa.Text(), nullable=True),
        sa.Column("shown_to", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url", "niche", name="uq_seen_urls_url_niche"),
        schema="buzzreach",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("seen_urls", schema="buzzreach")
