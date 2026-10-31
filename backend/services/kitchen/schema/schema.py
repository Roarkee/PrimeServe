from typing import Any
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

class MenuRoute(BaseModel):
    id : UUID
    restaurant_id: UUID
    station_id : UUID
    menu_item_id: UUID
    is_active: bool

