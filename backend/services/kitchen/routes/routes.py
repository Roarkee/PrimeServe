import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from ..database import SessionDep
from ..dependencies import require_permission
from ..exceptions import (AlreadyExistsError,InvalidStateTransitionError,KitchenValidationError,NotFoundError,)
from ..models import (KitchenItemStatus,KitchenTicketStatus,)
from ..schema.internal_schema import (KitchenOrderEvent,OrderEventResponse,)
from ..schema.schema import (
    MenuRouteCreate,
    MenuRouteResponse,
    PrepStationCreate,
    PrepStationResponse,
    KitchenTicketDetailResponse,
    TicketStatusUpdateRequest,
    RouteStatusUpdateRequest,
)
from ..services.kitchen_service import KitchenService
from ..services.menu_routing import create_menu_route
from ..services.order_comm_service import OrderEventService
from ..services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

kitchen_router = APIRouter(prefix="/kitchen", tags=["Kitchen"])
internal_router = APIRouter(prefix="/internal/kitchen", tags=["Internal Kitchen"])



# INTERNAL ROUTES (Inter-service communication from Orders)


@internal_router.post("/orders", response_model=OrderEventResponse)
async def receive_order_event(event: KitchenOrderEvent, session: SessionDep):
    """
    Receive an order event published by the Orders service outbox worker.
    Creates tickets, items, routes, and events atomically.
    Broadcasts ticket.created notification to KDS clients after commit.
    """
    try:
        result = OrderEventService.receive_order_created(session, event)

        # Broadcast ticket.created notification to connected KDS stations
        if result["status"] == "processed":
            message = {
                "event": "ticket.created",
                "data": {
                    "ticket_id": result["ticket_id"],
                },
            }

            restaurant_id_str = str(event.payload.order.restaurant_id)
            for station_id in result["station_ids"]:
                try:
                    await websocket_manager.broadcast_to_station(
                        restaurant_id=restaurant_id_str,
                        station_id=station_id,
                        message=message,
                    )
                except Exception as exc:
                    logger.warning("Failed to broadcast ticket.created to station %s: %s", station_id, exc)

        return OrderEventResponse(
            status=result["status"],
            duplicate=result["status"] == "duplicate",
            ticket_id=UUID(result["ticket_id"]) if result.get("ticket_id") else None,
        )

    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error processing internal order event: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal processing error")



# PREP STATIONS

@kitchen_router.post("/prep_stations", response_model=PrepStationResponse, status_code=status.HTTP_201_CREATED)
def create_prep_station(
    data: PrepStationCreate,
    session: SessionDep,
    user: dict = Depends(require_permission("kitchen:create")),
):
    """Create a new prep station for the authenticated restaurant."""
    restaurant_id = UUID(str(user["restaurant_id"]))
    try:
        return KitchenService.create_prep_station(session, data, restaurant_id)
    except AlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except KitchenValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@kitchen_router.get("/prep_stations", response_model=list[PrepStationResponse])
def list_prep_stations(
    session: SessionDep,
    is_active: bool | None = Query(default=None),
    user: dict = Depends(require_permission("kitchen:view")),
):
    """List prep stations for the authenticated restaurant."""
    restaurant_id = UUID(str(user["restaurant_id"]))
    return KitchenService.get_prep_stations(session, restaurant_id, is_active=is_active)


# MENU ROUTING


@kitchen_router.post("/menu_routes", response_model=MenuRouteResponse, status_code=status.HTTP_201_CREATED)
def create_menu_item_route(
    data: MenuRouteCreate,
    session: SessionDep,
    user: dict = Depends(require_permission("kitchen:create")),
):
    """Assign a menu item to a prep station for the authenticated restaurant."""
    restaurant_id = UUID(str(user["restaurant_id"]))
    try:
        return create_menu_route(
            session=session,
            restaurant_id=restaurant_id,
            station_id=data.station_id,
            menu_item_id=data.menu_item_id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except AlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


# KDS TICKET RETRIEVAL


@kitchen_router.get("/tickets/active", response_model=list[KitchenTicketDetailResponse])
def get_active_tickets(
    session: SessionDep,
    station_id: UUID | None = Query(default=None, description="Filter active tickets routed to this station"),
    user: dict = Depends(require_permission("kitchen:view")),
):
    """
    Retrieve active tickets (OPEN or IN_PROGRESS) for the authenticated restaurant.
    Used by KDS on connection or reconnect to hydrate the active ticket board.
    """
    restaurant_id = UUID(str(user["restaurant_id"]))
    return KitchenService.get_active_tickets(session, restaurant_id, station_id=station_id)


@kitchen_router.get("/tickets/{ticket_id}", response_model=KitchenTicketDetailResponse)
def get_ticket_details(
    ticket_id: UUID,
    session: SessionDep,
    user: dict = Depends(require_permission("kitchen:view")),
):
    """Retrieve full details of a single kitchen ticket."""
    restaurant_id = UUID(str(user["restaurant_id"]))
    try:
        return KitchenService.get_ticket_details(session, ticket_id, restaurant_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# TICKET LIFECYCLE MUTATIONS

async def _broadcast_ticket_update(restaurant_id: str, ticket_id: str, station_ids: list[str], payload: dict):
    """Helper to broadcast real-time updates to relevant KDS screens."""
    message = {
        "event": "ticket.updated",
        "data": {
            "ticket_id": ticket_id,
            **payload,
        },
    }
    for sid in station_ids:
        try:
            await websocket_manager.broadcast_to_station(
                restaurant_id=restaurant_id,
                station_id=sid,
                message=message,
            )
        except Exception as exc:
            logger.warning("Failed broadcasting ticket.updated to station %s: %s", sid, exc)


@kitchen_router.patch("/tickets/{ticket_id}/routes/{route_id}/status")
async def update_item_route_status(
    ticket_id: UUID,
    route_id: UUID,
    data: RouteStatusUpdateRequest,
    session: SessionDep,
    user: dict = Depends(require_permission("kitchen:update")),
):
    """Update preparation status for a specific station route of an item."""
    restaurant_id = UUID(str(user["restaurant_id"]))
    actor_id = UUID(str(user["sub"])) if user.get("sub") else None

    try:
        result = KitchenService.update_route_status(
            session=session,
            ticket_id=ticket_id,
            route_id=route_id,
            new_status=data.status,
            restaurant_id=restaurant_id,
            actor_employee_id=actor_id,
        )

        # Broadcast update to connected KDS stations
        await _broadcast_ticket_update(
            restaurant_id=str(restaurant_id),
            ticket_id=str(ticket_id),
            station_ids=result.get("station_ids", []),
            payload={
                "route_id": str(route_id),
                "station_id": result.get("station_id"),
                "status": result.get("status"),
                "ticket_status": result.get("ticket_status"),
            },
        )

        return result

    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidStateTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@kitchen_router.post("/tickets/{ticket_id}/routes/{route_id}/start")
async def start_item_route(
    ticket_id: UUID,
    route_id: UUID,
    session: SessionDep,
    user: dict = Depends(require_permission("kitchen:update")),
):
    """KDS convenience endpoint: start preparation on an item route."""
    return await update_item_route_status(
        ticket_id=ticket_id,
        route_id=route_id,
        data=RouteStatusUpdateRequest(status=KitchenItemStatus.IN_PROGRESS),
        session=session,
        user=user,
    )


@kitchen_router.post("/tickets/{ticket_id}/routes/{route_id}/ready")
async def ready_item_route(
    ticket_id: UUID,
    route_id: UUID,
    session: SessionDep,
    user: dict = Depends(require_permission("kitchen:update")),
):
    """KDS convenience endpoint: mark an item route as ready."""
    return await update_item_route_status(
        ticket_id=ticket_id,
        route_id=route_id,
        data=RouteStatusUpdateRequest(status=KitchenItemStatus.READY),
        session=session,
        user=user,
    )


@kitchen_router.patch("/tickets/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: UUID,
    data: TicketStatusUpdateRequest,
    session: SessionDep,
    user: dict = Depends(require_permission("kitchen:update")),
):
    """Update overall ticket status (e.g. IN_PROGRESS, READY, CANCELLED)."""
    restaurant_id = UUID(str(user["restaurant_id"]))
    actor_id = UUID(str(user["sub"])) if user.get("sub") else None

    try:
        result = KitchenService.update_ticket_status(
            session=session,
            ticket_id=ticket_id,
            new_status=data.status,
            restaurant_id=restaurant_id,
            actor_employee_id=actor_id,
        )

        await _broadcast_ticket_update(
            restaurant_id=str(restaurant_id),
            ticket_id=str(ticket_id),
            station_ids=result.get("station_ids", []),
            payload={"status": result.get("status")},
        )

        return result

    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidStateTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@kitchen_router.post("/tickets/{ticket_id}/ready")
async def ready_ticket(
    ticket_id: UUID,
    session: SessionDep,
    user: dict = Depends(require_permission("kitchen:update")),
):
    """KDS convenience endpoint: mark entire ticket ready."""
    return await update_ticket_status(
        ticket_id=ticket_id,
        data=TicketStatusUpdateRequest(status=KitchenTicketStatus.READY),
        session=session,
        user=user,
    )


@kitchen_router.post("/tickets/{ticket_id}/cancel")
async def cancel_ticket(
    ticket_id: UUID,
    session: SessionDep,
    user: dict = Depends(require_permission("kitchen:update")),
):
    """KDS convenience endpoint: cancel ticket."""
    return await update_ticket_status(
        ticket_id=ticket_id,
        data=TicketStatusUpdateRequest(status=KitchenTicketStatus.CANCELLED),
        session=session,
        user=user,
    )
