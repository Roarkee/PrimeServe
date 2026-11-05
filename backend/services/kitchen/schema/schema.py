from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from ..models import (
    KitchenTicketStatus,
    KitchenItemStatus,
    KitchenRoutingStatus,
)


class PrepStationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    is_active: bool = True
    display_order: int = 0


class PrepStationResponse(BaseModel):
    id: UUID
    restaurant_id: UUID
    branch_id: UUID | None = None
    name: str
    description: str | None = None
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MenuRouteCreate(BaseModel):
    station_id: UUID
    menu_item_id: UUID
    is_active: bool = True


class MenuRouteResponse(BaseModel):
    id: UUID
    restaurant_id: UUID
    station_id: UUID
    menu_item_id: UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KitchenTicketItemRouteResponse(BaseModel):
    id: UUID
    station_id: UUID
    station_name: str
    status: KitchenItemStatus
    started_at: datetime | None = None
    ready_at: datetime | None = None
    cancelled_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class KitchenTicketItemResponse(BaseModel):
    id: UUID
    ticket_id: UUID
    source_order_item_id: UUID
    menu_item_id: UUID | None = None
    item_name: str
    quantity: int
    modifiers: list[dict[str, Any]] = Field(default_factory=list)
    special_instructions: str | None = None
    allergens: list[str] = Field(default_factory=list)
    course_name: str | None = None
    status: KitchenItemStatus
    routing_status: KitchenRoutingStatus
    routes: list[KitchenTicketItemRouteResponse] = Field(default_factory=list)
    started_at: datetime | None = None
    ready_at: datetime | None = None
    cancelled_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class KitchenTicketDetailResponse(BaseModel):
    id: UUID
    restaurant_id: UUID
    source_order_id: UUID
    order_number: str | None = None
    order_type: str | None = None
    dining_option: str | None = None
    table_label: str | None = None
    customer_display_name: str | None = None
    special_instructions: str | None = None
    status: KitchenTicketStatus
    priority: int
    received_at: datetime
    started_at: datetime | None = None
    ready_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    items: list[KitchenTicketItemResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TicketStatusUpdateRequest(BaseModel):
    status: KitchenTicketStatus


class RouteStatusUpdateRequest(BaseModel):
    status: KitchenItemStatus


class ItemStatusUpdateRequest(BaseModel):
    status: KitchenItemStatus

