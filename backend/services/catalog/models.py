from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel,DateTime,UniqueConstraint

# auto_now =True equiv
def utc_now():
    return datetime.now(timezone.utc)

class MenuItemStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Category(SQLModel, table=True):
    __tablename__ = "categories"
    __table_args__ = {"schema": "prime_catalog"}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    restaurant_id: UUID
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=255)
    display_order: int = Field(default=0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now,nullable=False,sa_type=DateTime(timezone=True),)
    updated_at: datetime = Field(default_factory=utc_now,nullable=False,sa_type=DateTime(timezone=True),sa_column_kwargs={"onupdate":utc_now})


class MenuItem(SQLModel, table=True):
    __tablename__ = "menu_items"
    __table_args__ = {"schema": "prime_catalog"}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    restaurant_id: UUID
    category_id: UUID | None = Field(default=None, foreign_key="prime_catalog.categories.id",ondelete="SET NULL",)
    name: str = Field(max_length=150)
    description: str | None = Field(default=None, max_length=500)
    sku: str | None = Field(default=None, max_length=50)
    price: Decimal = Field(max_digits=10, decimal_places=2)
    status: MenuItemStatus = Field(default=MenuItemStatus.ACTIVE)
    image_path: str | None = Field(default=None, max_length=500)
    display_order: int = Field(default=0)
    created_at: datetime = Field(default_factory=utc_now,nullable=False,sa_type=DateTime(timezone=True),)
    updated_at: datetime = Field(default_factory=utc_now,nullable=False,sa_type=DateTime(timezone=True),sa_column_kwargs={"onupdate":utc_now})


class OptionGroup(SQLModel, table=True):
    __tablename__ = "option_groups"
    __table_args__ = {"schema": "prime_catalog"}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    restaurant_id: UUID
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=255)
    is_required: bool = Field(default=False)
    min_selections: int = Field(default=0)
    max_selections: int = Field(default=1)
    display_order: int = Field(default=0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now,nullable=False,sa_type=DateTime(timezone=True),)
    updated_at: datetime = Field(default_factory=utc_now,nullable=False,sa_type=DateTime(timezone=True),sa_column_kwargs={"onupdate":utc_now})




class MenuItemOptionGroup(SQLModel, table=True):
    __tablename__ = "menu_item_option_groups"
    __table_args__ = (UniqueConstraint("menu_item_id", "option_group_id", name="unique_menu_item_optionG"),{"schema": "prime_catalog"},)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    menu_item_id: UUID = Field(foreign_key="prime_catalog.menu_items.id",ondelete="CASCADE",)
    option_group_id: UUID = Field(foreign_key="prime_catalog.option_groups.id")
    display_order: int = Field(default=0)


class Option(SQLModel, table=True):
    __tablename__ = "options"
    __table_args__ = {"schema": "prime_catalog"}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    option_group_id: UUID = Field(foreign_key="prime_catalog.option_groups.id", ondelete="CASCADE")
    name: str = Field(max_length=100)
    additional_price: Decimal = Field(default=Decimal("0.00"), max_digits=10, decimal_places=2)
    display_order: int = Field(default=0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now,nullable=False,sa_type=DateTime(timezone=True),)
    updated_at: datetime = Field(default_factory=utc_now,nullable=False,sa_type=DateTime(timezone=True),sa_column_kwargs={"onupdate":utc_now})


