"""add uppercase item unrouted event

Revision ID: 97e1438f00a9
Revises: 8ee31496ad81
Create Date: 2026-10-31 03:18:40.956331

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '97e1438f00a9'
down_revision: Union[str, Sequence[str], None] = '8ee31496ad81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
    ALTER TYPE prime_kitchen.kitchen_event_type
    ADD VALUE IF NOT EXISTS 'ITEM_UNROUTED'
""")
    


def downgrade() -> None:
    """Downgrade schema."""
    pass
