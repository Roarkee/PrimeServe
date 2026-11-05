from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4
from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, Integer, JSON, String, Text, UniqueConstraint
from sqlmodel import Field, SQLModel


KITCHEN_SCHEMA = "prime_kitchen"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class KitchenTicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    CANCELLED = "cancelled"


class KitchenItemStatus(str, Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    CANCELLED = "cancelled"


class KitchenDeviceMode(str, Enum):
    ALL = "all"
    STATION = "station"
    EXPO = "expo"


class KitchenEventType(str, Enum):
    TICKET_CREATED = "ticket_created"
    ITEM_STARTED = "item_started"
    ITEM_READY = "item_ready"
    ITEM_CANCELLED = "item_cancelled"
    ITEM_UNROUTED = "item_unrouted"
    TICKET_RECALLED = "ticket_recalled"
    TICKET_READY = "ticket_ready"
    TICKET_CANCELLED = "ticket_cancelled"
    ORDER_UPDATED = "order_updated"

class KitchenRoutingStatus(str, Enum):
    UNROUTED = "unrouted"
    ROUTED = "routed"
    MANUALLY_ASSIGNED = "manually_assigned"

class PrepStation(SQLModel, table=True):
    __tablename__ = "prep_stations"
    __table_args__ = (
        UniqueConstraint("restaurant_id", "branch_id", "name", name="uq_prep_station_restaurant_branch_name"),
        {"schema": KITCHEN_SCHEMA},
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    restaurant_id: UUID = Field(index=True)
    branch_id: UUID | None = Field(default=None, index=True)
    name: str = Field(sa_type=String(100))
    description: str | None = Field(default=None, sa_type=Text)
    is_active: bool = Field(default=True, sa_type=Boolean)
    display_order: int = Field(default=0, sa_type=Integer)
    created_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))
    updated_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True),sa_column_kwargs={"onupdate":utc_now})


class MenuItemRouting(SQLModel, table=True):
    __tablename__ = "menu_item_routings"
    __table_args__ = (
        UniqueConstraint("restaurant_id", "menu_item_id", "station_id", name="uq_menu_item_station_route"),
        {"schema": KITCHEN_SCHEMA},
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    restaurant_id: UUID = Field(index=True)
    menu_item_id: UUID = Field(index=True)
    station_id: UUID = Field(foreign_key=f"{KITCHEN_SCHEMA}.prep_stations.id", index=True)
    is_active: bool = Field(default=True, sa_type=Boolean)
    created_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))


class KitchenTicket(SQLModel, table=True):
    __tablename__ = "kitchen_tickets"
    __table_args__ = (
        UniqueConstraint("source_order_id", name="uq_kitchen_ticket_source_order"),
        {"schema": KITCHEN_SCHEMA},
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    restaurant_id: UUID = Field(index=True)
    branch_id: UUID | None = Field(default=None, index=True)
    source_order_id: UUID = Field(index=True, unique=True)
    order_number: str | None = Field(default=None, sa_type=String(50))
    order_type: str | None = Field(default=None, sa_type=String(40))
    dining_option: str | None = Field(default=None, sa_type=String(40))
    table_label: str | None = Field(default=None, sa_type=String(80))
    customer_display_name: str | None = Field(default=None, sa_type=String(100))
    special_instructions: str | None = Field(default=None, sa_type=Text)
    status: KitchenTicketStatus = Field(default=KitchenTicketStatus.OPEN, sa_column=Column(SAEnum(KitchenTicketStatus, name="kitchen_ticket_status", schema=KITCHEN_SCHEMA), nullable=False, default=KitchenTicketStatus.OPEN))
    priority: int = Field(default=0, sa_type=Integer)
    source_order_version: int = Field(default=1, sa_type=Integer)
    received_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))
    started_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    ready_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    cancelled_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    created_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))
    updated_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True),sa_column_kwargs={"onupdate":utc_now})


class KitchenTicketItem(SQLModel, table=True):
    __tablename__ = "kitchen_ticket_items"
    __table_args__ = (
        UniqueConstraint("ticket_id", "source_order_item_id", name="uq_ticket_source_order_item"),
        {"schema": KITCHEN_SCHEMA},
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    ticket_id: UUID = Field(foreign_key=f"{KITCHEN_SCHEMA}.kitchen_tickets.id", index=True)
    source_order_item_id: UUID = Field(index=True)
    menu_item_id: UUID | None = Field(default=None, index=True)
    item_name: str = Field(sa_type=String(200))
    quantity: int = Field(gt=0, sa_type=Integer)
    modifiers: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON, nullable=False, default=list))
    special_instructions: str | None = Field(default=None, sa_type=Text)
    allergens: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False, default=list))
    course_name: str | None = Field(default=None, sa_type=String(80))
    status: KitchenItemStatus = Field(default=KitchenItemStatus.QUEUED, sa_column=Column(SAEnum(KitchenItemStatus, name="kitchen_item_status", schema=KITCHEN_SCHEMA), nullable=False, default=KitchenItemStatus.QUEUED))
    started_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    ready_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    cancelled_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    created_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))
    updated_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True),sa_column_kwargs={"onupdate":utc_now})
    routing_status: KitchenRoutingStatus = Field(
        default=KitchenRoutingStatus.UNROUTED,
        sa_column=Column(
            SAEnum(KitchenRoutingStatus, name="kitchenroutingstatus", schema=KITCHEN_SCHEMA),
            nullable=False,
            default=KitchenRoutingStatus.UNROUTED,
        ),
    )

class KitchenDevice(SQLModel, table=True):
    __tablename__ = "kitchen_devices"
    __table_args__ = (
        UniqueConstraint("restaurant_id", "device_key", name="uq_kitchen_device_restaurant_key"),
        {"schema": KITCHEN_SCHEMA},
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    restaurant_id: UUID = Field(index=True)
    branch_id: UUID | None = Field(default=None, index=True)
    name: str = Field(sa_type=String(100))
    device_key: str = Field(sa_type=String(100))
    mode: KitchenDeviceMode = Field(default=KitchenDeviceMode.ALL, sa_column=Column(SAEnum(KitchenDeviceMode, name="kitchen_device_mode", schema=KITCHEN_SCHEMA), nullable=False, default=KitchenDeviceMode.ALL))
    station_id: UUID | None = Field(default=None, foreign_key=f"{KITCHEN_SCHEMA}.prep_stations.id", index=True)
    display_options: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False, default=dict))
    is_active: bool = Field(default=True, sa_type=Boolean)
    created_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))
    updated_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True),sa_column_kwargs={"onupdate":utc_now})


class KitchenEvent(SQLModel, table=True):
    __tablename__ = "kitchen_events"
    __table_args__ = {"schema": KITCHEN_SCHEMA}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    restaurant_id: UUID = Field(index=True)
    branch_id: UUID | None = Field(default=None, index=True)
    ticket_id: UUID | None = Field(default=None, foreign_key=f"{KITCHEN_SCHEMA}.kitchen_tickets.id", index=True)
    ticket_item_id: UUID | None = Field(default=None, foreign_key=f"{KITCHEN_SCHEMA}.kitchen_ticket_items.id", index=True)
    event_type: KitchenEventType = Field(sa_column=Column(SAEnum(KitchenEventType, name="kitchen_event_type", schema=KITCHEN_SCHEMA), nullable=False))
    actor_employee_id: UUID | None = Field(default=None, index=True)
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False, default=dict))
    created_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))




class KitchenTicketItemRoute(SQLModel, table=True):
    __tablename__ = "kitchen_ticket_item_routes"
    __table_args__ = (
        UniqueConstraint("ticket_item_id", "station_id", name="uq_ticket_item_station_route"),
        {"schema": KITCHEN_SCHEMA},
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    restaurant_id: UUID = Field(index=True)
    branch_id: UUID | None = Field(default=None, index=True)
    ticket_item_id: UUID = Field(foreign_key=f"{KITCHEN_SCHEMA}.kitchen_ticket_items.id", index=True)
    station_id: UUID = Field(foreign_key=f"{KITCHEN_SCHEMA}.prep_stations.id", index=True)
    status: KitchenItemStatus = Field(default=KitchenItemStatus.QUEUED, sa_column=Column(SAEnum(KitchenItemStatus, name="kitchen_item_route_status", schema=KITCHEN_SCHEMA), nullable=False, default=KitchenItemStatus.QUEUED))
    started_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    ready_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    station_name: str = Field(sa_type=String(100))
    cancelled_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    created_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))
    updated_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True),sa_column_kwargs={"onupdate":utc_now})







class ProcessedEvent(SQLModel, table=True):
    __tablename__ = "processed_events"
    __table_args__ = (
        {"schema": "prime_kitchen"},
    )

    id: UUID = Field(primary_key=True)
    event_type: str = Field(max_length=100, nullable=False)
    aggregate_id: UUID = Field(nullable=False)
    aggregate_version: int = Field(ge=1, nullable=False)
    processed_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
    )














