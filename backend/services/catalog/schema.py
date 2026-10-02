
from uuid import UUID
from pydantic import BaseModel,Field
from datetime import datetime
from decimal import Decimal
from .models import MenuItemStatus

class CategoryCreate(BaseModel):
    name: str
    description: str | None = None
    display_order: int = 0


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    display_order: int | None = None
    is_active: bool | None = None


class CategoryReorder(BaseModel):
    display_order: int

class CategoryResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    restaurant_id: UUID


class MenuItemCreate(BaseModel):
    category_id: UUID | None = None
    name: str = Field(max_length=150)
    description: str | None = Field(default=None, max_length=500)
    sku: str | None = Field(default=None, max_length=50)
    price: Decimal
    status: MenuItemStatus = MenuItemStatus.ACTIVE
    image_path: str | None = Field(default=None, max_length=500)
    display_order: int = 0


class MenuItemUpdate(BaseModel):
    category_id: UUID | None = None
    name: str | None = Field(default=None, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    sku: str | None = Field(default=None, max_length=50)
    price: Decimal | None = None
    status: MenuItemStatus | None = None
    image_path: str | None = Field(default=None, max_length=500)
    display_order: int | None = None


class MenuItemResponse(BaseModel):
    id: UUID
    category_id: UUID | None
    name: str
    description: str | None
    sku: str | None
    price: Decimal
    status: MenuItemStatus
    image_path: str | None
    display_order: int
    created_at: datetime
    updated_at: datetime


class OptionGroupCreate(BaseModel):
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=255)
    is_required: bool = False
    min_selections: int = 0
    max_selections: int = 1
    display_order: int = 0
    is_active: bool = True


class OptionGroupUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    is_required: bool | None = None
    min_selections: int | None = None
    max_selections: int | None = None
    display_order: int | None = None
    is_active: bool | None = None


class OptionGroupResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    is_required: bool
    min_selections: int
    max_selections: int
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

class OptionCreate(BaseModel):
    option_group_id: UUID
    name: str = Field(max_length=100)
    additional_price: Decimal = Decimal("0.00")
    display_order: int = 0
    is_active: bool = True


class OptionUpdate(BaseModel):
    option_group_id: UUID | None = None
    name: str | None = Field(default=None, max_length=100)
    additional_price: Decimal | None = None
    display_order: int | None = None
    is_active: bool | None = None


class OptionResponse(BaseModel):
    id: UUID
    option_group_id: UUID
    name: str
    additional_price: Decimal
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime



class MenuItemOptionGroupCreate(BaseModel):
    menu_item_id: UUID
    option_group_id: UUID
    display_order: int = 0


class MenuItemOptionGroupUpdate(BaseModel):
    display_order: int | None = None


class MenuItemOptionGroupResponse(BaseModel):
    id: UUID
    menu_item_id: UUID
    option_group_id: UUID
    display_order: int

class MenuOptionResponse(BaseModel):
    id: UUID
    name: str
    additional_price: Decimal
    display_order: int


class MenuOptionGroupResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    is_required: bool
    min_selections: int
    max_selections: int
    display_order: int
    options: list[MenuOptionResponse]


class MenuItemMenuResponse(BaseModel):
    id: UUID
    category_id: UUID | None
    name: str
    description: str | None
    sku: str | None
    price: Decimal
    status: MenuItemStatus
    image_path: str | None
    display_order: int
    option_groups: list[MenuOptionGroupResponse]


class CategoryMenuResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    display_order: int
    items: list[MenuItemMenuResponse]


class MenuResponse(BaseModel):
    categories: list[CategoryMenuResponse]