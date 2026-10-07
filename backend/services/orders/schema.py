from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field
from .models import OrderType,OrderStatus,OrderItemStatus
from datetime import datetime


class OrderItemCreate(BaseModel):
    menu_item_id: UUID
    quantity: int = Field(gt=0)
    option_ids: list[UUID] = []
    notes: str | None = Field(default=None, max_length=500)


class OrderCreate(BaseModel):
    order_type: OrderType
    items: list[OrderItemCreate]
    notes: str | None = Field(default=None, max_length=500)



class OrderItemOptionResponse(BaseModel):
    id: UUID
    option_id: UUID
    name: str
    additional_price: Decimal
    quantity: int


class OrderItemResponse(BaseModel):
    id: UUID
    menu_item_id: UUID
    name: str
    unit_price: Decimal
    quantity: int
    subtotal: Decimal
    notes: str | None
    status: OrderItemStatus
    options: list[OrderItemOptionResponse]


class OrderResponse(BaseModel):
    id: UUID
    order_number: int
    order_type: OrderType
    status: OrderStatus
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal
    notes: str | None
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime


class CatalogValidationItem(BaseModel):
    menu_item_id: UUID
    quantity: int
    option_ids: list[UUID] = []


class CatalogValidationRequest(BaseModel):
    restaurant_id: UUID
    items: list[CatalogValidationItem]


class CatalogValidatedOption(BaseModel):
    option_id: UUID
    name: str
    additional_price: Decimal


class CatalogValidatedItem(BaseModel):
    menu_item_id: UUID
    name: str
    price: Decimal
    quantity: int
    options: list[CatalogValidatedOption]


class CatalogValidationResponse(BaseModel):
    items: list[CatalogValidatedItem]


class OrderListResponse(BaseModel):
    id: UUID
    order_number: int
    order_type: OrderType
    status: OrderStatus
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal
    notes: str | None
    created_at: datetime
    updated_at: datetime


class OrderUpdate(BaseModel):
    status: OrderStatus | None = None
    order_type: OrderType | None = None
    notes: str | None = None

class PaginatedOrderResponse(BaseModel):
    items: list[OrderListResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
