from datetime import datetime, timezone,date
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, DateTime,UniqueConstraint


def utc_now():
    return datetime.now(timezone.utc)


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class OrderItemStatus(str, Enum):
    PENDING = "pending"
    PREPARING = "preparing"
    READY = "ready"
    CANCELLED = "cancelled"

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
    status: OrderItemStatus = Field(default=OrderItemStatus.PENDING)
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






