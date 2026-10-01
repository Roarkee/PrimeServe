
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

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
