from .services.order_service import OrderService
from fastapi.routing import APIRouter
from fastapi import Depends
from .schema import (OrderCreate,
                     OrderItemCreate,
                     OrderResponse,
                     OrderItemResponse,
                     OrderItemOptionResponse,
                     CatalogValidationResponse,
                     CatalogValidationRequest,
                     OrderListResponse,
                     OrderUpdate,
                     PaginatedOrderResponse
                     )
from .models import OrderType, OrderStatus

from .database import SessionDep
from .dependencies import require_permission

router = APIRouter(tags=["Order Service"])

@router.post("/order/create", response_model=OrderResponse)
def create_order(session:SessionDep, data:OrderCreate, user=Depends(require_permission("order:create"))):
    return OrderService.create_order(session, data, user["restaurant_id"])

@router.get("/order", response_model=PaginatedOrderResponse)
def get_orders(session:SessionDep,status: OrderStatus | None = None,
    order_type: OrderType | None = None,
    page: int = 1,
    page_size: int = 20, user=Depends(require_permission("order:view"))):

    return OrderService.get_orders(session,user["restaurant_id"],
        status=status,
        order_type=order_type,
        page=page,
        page_size=page_size,)


@router.get("/order/{pk}", response_model=OrderResponse)
def get_order(pk, session:SessionDep, user=Depends(require_permission("order:view"))):
    return OrderService.get_order(pk, session, user["restaurant_id"])

@router.patch("/order/{pk}", response_model=OrderListResponse)
def update_order(pk, session:SessionDep,data:OrderUpdate, user=Depends(require_permission("order:update")),):
    return OrderService.update_order(pk, session,user["restaurant_id"], data)