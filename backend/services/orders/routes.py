from .services.order_service import OrderService
from fastapi.routing import APIRouter
from fastapi import Depends
from .schema import (OrderCreate,
                     OrderItemCreate,
                     OrderResponse,
                     OrderItemResponse,
                     OrderItemOptionResponse,
                     CatalogValidationResponse,
                     CatalogValidationRequest)

from .database import SessionDep
from .dependencies import require_permission

router = APIRouter(tags=["Order Service"])

@router.post("/order/create", response_model=OrderResponse)
def create_order(session:SessionDep, data:OrderCreate, user=Depends(require_permission("order:create"))):
    return OrderService.create_order(session, data, user["restaurant_id"])