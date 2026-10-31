from fastapi import HTTPException,APIRouter,Depends
from .database import SessionDep
from .schema.internal_schema import KitchenOrderEvent, OrderEventResponse
from .services.order_comm_service import OrderEventService
from .dependencies import get_user


router = APIRouter(prefix="/kitchen", tags=["Kitchen House"])
internal_router = APIRouter(prefix="/internal/kitchen", tags=["Internal Kitchen"])



@internal_router.post("/orders", response_model=OrderEventResponse)
def receive_order_event(event: KitchenOrderEvent, session: SessionDep,user=Depends(get_user)):
    try:
        result = OrderEventService.receive_order_created(session, event)

        return OrderEventResponse(
            status="processed",
            duplicate=result["duplicate"],
            ticket_id=result.get("ticket_id"),
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))