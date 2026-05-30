"""add_stripe_customer

Revision ID: b1c2d3e4f5a6
Revises: a3c7f1e29b04
Create Date: 2026-05-31 22:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: str | Sequence[str] | None = "a3c7f1e29b04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "stripe_customers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=False),
        sa.Column(
            "stripe_subscription_id", sa.String(length=255), nullable=True
        ),
        sa.Column("plan_id", sa.String(length=255), nullable=True),
        sa.Column(
            "subscription_status",
            sa.String(length=20),
            nullable=False,
            server_default="none",
        ),
        sa.Column(
            "current_period_end", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["buzzreach.users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stripe_customer_id"),
        sa.UniqueConstraint("user_id"),
        schema="buzzreach",
    )
    op.create_index(
        "ix_stripe_customers_user_id",
        "stripe_customers",
        ["user_id"],
        schema="buzzreach",
    )
    op.create_index(
        "ix_stripe_customers_stripe_customer_id",
        "stripe_customers",
        ["stripe_customer_id"],
        schema="buzzreach",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_stripe_customers_stripe_customer_id",
        table_name="stripe_customers",
        schema="buzzreach",
    )
    op.drop_index(
        "ix_stripe_customers_user_id",
        table_name="stripe_customers",
        schema="buzzreach",
    )
    op.drop_table("stripe_customers", schema="buzzreach")
