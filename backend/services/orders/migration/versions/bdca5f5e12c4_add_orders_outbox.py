
"""add orders outbox

Revision ID: bdca5f5e12c4
Revises: 77dedd2ffc36
Create Date: 2026-10-30 03:34:07.577266

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'bdca5f5e12c4'
down_revision: Union[str, Sequence[str], None] = '77dedd2ffc36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        'outbox_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('aggregate_type', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('aggregate_id', sa.Uuid(), nullable=False),
        sa.Column('event_type', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('aggregate_version', sa.Integer(), nullable=True),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False),
        sa.Column('available_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.Column('created_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.Column('published_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=True),
        sa.Column('locked_until', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='prime_orders'
    )

    op.create_index(
        'ix_outbox_aggregate',
        'outbox_events',
        ['aggregate_type', 'aggregate_id'],
        unique=False,
        schema='prime_orders'
    )

    op.create_index(
        'ix_outbox_status_available',
        'outbox_events',
        ['status', 'available_at'],
        unique=False,
        schema='prime_orders'
    )

    op.add_column(
        'orders',
        sa.Column('revision', sa.Integer(), nullable=False, server_default='1'),
        schema='prime_orders'
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column('orders', 'revision', schema='prime_orders')

    op.drop_index(
        'ix_outbox_status_available',
        table_name='outbox_events',
        schema='prime_orders'
    )

    op.drop_index(
        'ix_outbox_aggregate',
        table_name='outbox_events',
        schema='prime_orders'
    )

    op.drop_table('outbox_events', schema='prime_orders')
