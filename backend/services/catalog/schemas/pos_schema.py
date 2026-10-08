from pydantic import BaseModel,Field
from decimal import Decimal
from ..models import MenuItemStatus
from uuid import UUID
from .management_schema import CategoryCreate


class MenuOptionCreate(BaseModel):
    name: str = Field(max_length=100)
    additional_price: Decimal = Decimal("0.00")
    display_order: int = 0
    is_active: bool = True


class MenuOptionGroupCreate(BaseModel):
    option_group_id: UUID | None = None
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=255)
    is_required: bool = False
    min_selections: int = 0
    max_selections: int = 1
    display_order: int = 0
    is_active: bool = True
    options: list[MenuOptionCreate] = Field(default_factory=list)


class MenuItemMenuCreate(BaseModel):
    name: str = Field(max_length=150)
    description: str | None = Field(default=None, max_length=500)
    sku: str | None = Field(default=None, max_length=50)
    price: Decimal
    status: MenuItemStatus = MenuItemStatus.ACTIVE
    image_path: str | None = Field(default=None, max_length=500)
    display_order: int = 0
    option_groups: list[MenuOptionGroupCreate] = Field(default_factory=list)


class MenuCreate(BaseModel):
    category_id: UUID | None = None
    category: CategoryCreate | None = None
    menu_item: MenuItemMenuCreate