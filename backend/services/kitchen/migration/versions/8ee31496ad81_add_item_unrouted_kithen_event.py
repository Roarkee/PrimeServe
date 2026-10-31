
"""add item unrouted kitchen event

Revision ID: 8ee31496ad81
Revises: 38df750d37d8
Create Date: 2026-10-31 01:35:40.168118
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "8ee31496ad81"
down_revision: Union[str, Sequence[str], None] = "38df750d37d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create processed events table.
    op.create_table(
        "processed_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("aggregate_id", sa.Uuid(), nullable=False),
        sa.Column("aggregate_version", sa.Integer(), nullable=False),
        sa.Column("processed_at", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="prime_kitchen",
    )

    # Add the new value to the existing KitchenEventType enum.
    op.execute("""
        ALTER TYPE prime_kitchen.kitchen_event_type
        ADD VALUE IF NOT EXISTS 'item_unrouted'
    """)

    # Create the routing status enum before using it.
    routing_status_enum = sa.Enum(
        "UNROUTED",
        "ROUTED",
        "MANUALLY_ASSIGNED",
        name="kitchenroutingstatus",
        schema="prime_kitchen",
    )

    routing_status_enum.create(op.get_bind(), checkfirst=True)

    # Add routing_status with a temporary default for existing rows.
    op.add_column(
        "kitchen_ticket_items",
        sa.Column(
            "routing_status",
            routing_status_enum,
            nullable=False,
            server_default="UNROUTED",
        ),
        schema="prime_kitchen",
    )

    # Remove the database-level default after backfilling existing rows.
    op.alter_column(
        "kitchen_ticket_items",
        "routing_status",
        server_default=None,
        schema="prime_kitchen",
    )

    # Ensure source_order_id has a unique index.
    op.drop_index(
        op.f("ix_prime_kitchen_kitchen_tickets_source_order_id"),
        table_name="kitchen_tickets",
        schema="prime_kitchen",
    )

    op.create_index(
        op.f("ix_prime_kitchen_kitchen_tickets_source_order_id"),
        "kitchen_tickets",
        ["source_order_id"],
        unique=True,
        schema="prime_kitchen",
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_prime_kitchen_kitchen_tickets_source_order_id"),
        table_name="kitchen_tickets",
        schema="prime_kitchen",
    )

    op.create_index(
        op.f("ix_prime_kitchen_kitchen_tickets_source_order_id"),
        "kitchen_tickets",
        ["source_order_id"],
        unique=False,
        schema="prime_kitchen",
    )

    op.drop_column(
        "kitchen_ticket_items",
        "routing_status",
        schema="prime_kitchen",
    )

    op.execute("""
        DROP TYPE IF EXISTS prime_kitchen.kitchenroutingstatus
    """)

    op.drop_table("processed_events", schema="prime_kitchen")


