"""add_email_verification

Revision ID: c4a1e2f30b01
Revises: b1c2d3e4f5a6
Create Date: 2026-05-31 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c4a1e2f30b01'
down_revision: str | Sequence[str] = 'b1c2d3e4f5a6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add email_verified column to users and email_tokens table."""
    op.add_column(
        'users',
        sa.Column(
            'email_verified',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('0'),
        ),
        schema='buzzreach',
    )

    op.create_table(
        'email_tokens',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('email', sa.String(length=254), nullable=False),
        sa.Column('token', sa.String(length=64), nullable=False),
        sa.Column(
            'token_type',
            sa.Enum('verification', 'password_reset', name='token_type_enum'),
            nullable=False,
        ),
        sa.Column('used', sa.Boolean(), nullable=False),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), nullable=False,
        ),
        sa.Column(
            'expires_at', sa.DateTime(timezone=True), nullable=False,
        ),
        sa.ForeignKeyConstraint(['user_id'], ['buzzreach.users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token'),
        schema='buzzreach',
    )


def downgrade() -> None:
    """Remove email_tokens table and email_verified column."""
    op.drop_table('email_tokens', schema='buzzreach')
    op.drop_column('users', 'email_verified', schema='buzzreach')
