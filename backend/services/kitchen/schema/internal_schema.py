
from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OrderEventResponse(BaseModel):
    status: str
    duplicate: bool
    ticket_id: UUID | None = None


class KitchenOrderOption(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    option_id: UUID
    name: str
    additional_price: Decimal
    quantity: int = Field(gt=0)


class KitchenOrderItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    menu_item_id: UUID
    name: str
    unit_price: Decimal
    quantity: int = Field(gt=0)
    subtotal: Decimal
    notes: str | None = None
    options: list[KitchenOrderOption] = Field(default_factory=list)


class KitchenOrderSnapshot(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    restaurant_id: UUID
    order_number: int
    order_type: str
    status: str
    revision: int = Field(ge=1)
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    items: list[KitchenOrderItem]


class KitchenOrderPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    order: KitchenOrderSnapshot


class KitchenOrderEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    event_type: str = Field(min_length=1, max_length=100)
    aggregate_type: str = Field(min_length=1, max_length=50)
    aggregate_id: UUID
    aggregate_version: int = Field(ge=1)
    payload: KitchenOrderPayload

    @model_validator(mode="after")
    def validate_order_identity(self):
        order = self.payload.order

        if self.aggregate_type != "order":
            raise ValueError("Expected aggregate_type 'order'")

        if self.aggregate_id != order.id:
            raise ValueError("Event aggregate_id does not match order ID")

        if self.aggregate_version != order.revision:
            raise ValueError("Event version does not match order revision")

        return self
