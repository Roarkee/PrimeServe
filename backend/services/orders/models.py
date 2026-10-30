from datetime import datetime, timezone,date
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4
from typing import Any
from sqlalchemy import Column, Index, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel, DateTime,UniqueConstraint


def utc_now():
    return datetime.now(timezone.utc)


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# class OrderItemStatus(str, Enum):
#     PENDING = "pending"
#     PREPARING = "preparing"
#     READY = "ready"
#     CANCELLED = "cancelled"

class OrderType(str, Enum):
    DINE_IN = "dine_in"
    TAKEAWAY = "takeaway"
    DELIVERY = "delivery"


class Order(SQLModel, table=True):
    __tablename__ = "orders"
    __table_args__ = (
    
    {"schema": "prime_orders"},
)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    restaurant_id: UUID
    order_number: int
    order_type: OrderType
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    subtotal: Decimal = Field(max_digits=12, decimal_places=2)
    discount: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    tax: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    total: Decimal = Field(max_digits=12, decimal_places=2)
    notes: str | None = Field(default=None, max_length=500)
    revision: int = Field(default=1, ge=1, sa_type=Integer, nullable=False)
    created_at: datetime = Field(default_factory=utc_now, nullable=False, sa_type=DateTime(timezone=True))
    updated_at: datetime = Field(default_factory=utc_now, nullable=False, sa_type=DateTime(timezone=True), sa_column_kwargs={"onupdate": utc_now})




class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"
    __table_args__ = {"schema": "prime_orders"}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    order_id: UUID = Field(foreign_key="prime_orders.orders.id",ondelete="CASCADE",)
    menu_item_id: UUID
    name: str = Field(max_length=150)
    unit_price: Decimal = Field(max_digits=10,decimal_places=2,)
    quantity: int
    subtotal: Decimal = Field(max_digits=12,decimal_places=2,)
    notes: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=utc_now,nullable=False,sa_type=DateTime(timezone=True),)



class OrderItemOption(SQLModel, table=True):
    __tablename__ = "order_item_options"
    __table_args__ = {"schema": "prime_orders"}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    order_item_id: UUID = Field(foreign_key="prime_orders.order_items.id",ondelete="CASCADE",)
    option_id: UUID
    name: str = Field(max_length=100)
    additional_price: Decimal = Field(max_digits=10,decimal_places=2,)
    quantity: int = Field(default=1)

class OrderNumberCounter(SQLModel, table=True):
    __tablename__ = "order_number_counters"

    __table_args__ = (
        UniqueConstraint(
            "restaurant_id",
            "counter_date",
            name="unique_restaurant_counter_date",
        ),
        {"schema": "prime_orders"},
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    restaurant_id: UUID
    counter_date: date
    last_number: int = Field(default=0)



class OutboxEvent(SQLModel, table=True):
    __tablename__ = "outbox_events"
    __table_args__ = (
        Index("ix_outbox_status_available", "status", "available_at"),
        Index("ix_outbox_aggregate", "aggregate_type", "aggregate_id"),
        {"schema": "prime_orders"},
        Index(
            "uq_outbox_aggregate_version",
            "aggregate_type",
            "aggregate_id",
            "aggregate_version",
            unique=True,
            )
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    aggregate_type: str = Field(max_length=50, nullable=False)
    aggregate_id: UUID = Field(nullable=False)
    event_type: str = Field(max_length=100, nullable=False)
    aggregate_version: int = Field(ge=1, nullable=False)
    payload: dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))
    status: str = Field(default="pending", max_length=20, nullable=False)
    attempts: int = Field(default=0, sa_type=Integer, ge=0, nullable=False)
    available_at: datetime = Field(default_factory=utc_now, nullable=False)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    published_at: datetime | None = Field(default=None)
    locked_until: datetime | None = Field(default=None)
    last_error: str | None = Field(default=None, sa_type=Text)
    locked_by: str | None = Field(default=None, max_length=100)






