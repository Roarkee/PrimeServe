from fastapi import HTTPException,APIRouter,Depends
from .database import SessionDep
from .schema.internal_schema import KitchenOrderEvent, OrderEventResponse
from .services.order_comm_service import OrderEventService
from .dependencies import require_permission
from .schema.schema import MenuRoute
from .services.menu_routing import create_menu_route


kitchen_router = APIRouter(prefix="/kitchen", tags=["Kitchen House"])
internal_router = APIRouter(prefix="/internal/kitchen", tags=["Internal Kitchen"])

# INTERNAL ROUTES
@internal_router.post("/orders", response_model=OrderEventResponse)
def receive_order_event(event: KitchenOrderEvent, session: SessionDep):
    try:
        result = OrderEventService.receive_order_created(session, event)

        return OrderEventResponse(
            status=result["status"],
            duplicate=result["status"] == "duplicate",
            ticket_id=result.get("ticket_id"),
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# KITCHEN ROUTES
@kitchen_router.post("/menu_route")
def create_menu_item_route(session:SessionDep, data: MenuRoute, user=Depends(require_permission("kitchen:create"))):
    data = data.model_dump()
    route = create_menu_route(session, user["restaurant_id"],data.station_id,data.menu_item_id)
    return route