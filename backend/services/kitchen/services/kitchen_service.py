import logging
from datetime import datetime, timezone
from uuid import UUID
from collections import defaultdict
from sqlmodel import Session, select

from ..models import (
    PrepStation,
    KitchenTicket,
    KitchenTicketItem,
    KitchenTicketItemRoute,
    KitchenEvent,
    KitchenEventType,
    KitchenTicketStatus,
    KitchenItemStatus,
)
from ..schema.schema import (
    PrepStationCreate,
    KitchenTicketDetailResponse,
    KitchenTicketItemResponse,
    KitchenTicketItemRouteResponse,
)
from ..exceptions import (
    NotFoundError,
    InvalidStateTransitionError,
    AlreadyExistsError,
)

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class KitchenService:


    # Prep Station Operations

    @staticmethod
    def create_prep_station(
        session: Session,
        data: PrepStationCreate,
        restaurant_id: UUID,
    ) -> PrepStation:
        """Create a new prep station for the restaurant."""
        # Ensure station name is unique for this restaurant
        existing = session.exec(
            select(PrepStation).where(
                PrepStation.restaurant_id == restaurant_id,
                PrepStation.name == data.name,
            )
        ).first()

        if existing:
            raise AlreadyExistsError(f"Prep station with name '{data.name}' already exists")

        station = PrepStation(
            restaurant_id=restaurant_id,
            name=data.name,
            description=data.description,
            is_active=data.is_active,
            display_order=data.display_order,
        )
        session.add(station)
        session.commit()
        session.refresh(station)
        return station

    @staticmethod
    def get_prep_stations(
        session: Session,
        restaurant_id: UUID,
        is_active: bool | None = None,
    ) -> list[PrepStation]:
        """Fetch all prep stations for the restaurant, optionally filtering by active state."""
        query = select(PrepStation).where(PrepStation.restaurant_id == restaurant_id)
        if is_active is not None:
            query = query.where(PrepStation.is_active == is_active)
        query = query.order_by(PrepStation.display_order, PrepStation.name)
        return list(session.exec(query).all())

    # Ticket Retrieval for KDS

    @staticmethod
    def get_active_tickets(
        session: Session,
        restaurant_id: UUID,
        station_id: UUID | None = None,
    ) -> list[KitchenTicketDetailResponse]:
        """
        Fetch active kitchen tickets (status in OPEN, IN_PROGRESS).
        If station_id is provided, only tickets having items routed to that station are returned.
        Batches queries to prevent N+1 query overhead.
        """

        if station_id:
     
            query = (
                select(KitchenTicket)
                .join(KitchenTicketItem, KitchenTicketItem.ticket_id == KitchenTicket.id)
                .join(KitchenTicketItemRoute, KitchenTicketItemRoute.ticket_item_id == KitchenTicketItem.id)
                .where(
                    KitchenTicket.restaurant_id == restaurant_id,
                    KitchenTicket.status.in_([KitchenTicketStatus.OPEN, KitchenTicketStatus.IN_PROGRESS]),
                    KitchenTicketItemRoute.station_id == station_id,
                )
                .distinct()
                .order_by(KitchenTicket.priority.desc(), KitchenTicket.received_at.asc())
            )
        else:
            query = (
                select(KitchenTicket)
                .where(
                    KitchenTicket.restaurant_id == restaurant_id,
                    KitchenTicket.status.in_([KitchenTicketStatus.OPEN, KitchenTicketStatus.IN_PROGRESS]),
                )
                .order_by(KitchenTicket.priority.desc(), KitchenTicket.received_at.asc())
            )

        tickets = list(session.exec(query).all())
        if not tickets:
            return []

        return KitchenService._hydrate_tickets(session, tickets)

    @staticmethod
    def get_ticket_details(
        session: Session,
        ticket_id: UUID,
        restaurant_id: UUID,
    ) -> KitchenTicketDetailResponse:
        """Fetch full details of a specific kitchen ticket."""
        ticket = session.exec(
            select(KitchenTicket).where(
                KitchenTicket.id == ticket_id,
                KitchenTicket.restaurant_id == restaurant_id,
            )
        ).first()

        if ticket is None:
            raise NotFoundError(f"Kitchen ticket {ticket_id} not found")

        hydrated = KitchenService._hydrate_tickets(session, [ticket])
        return hydrated[0]

    @staticmethod
    def _hydrate_tickets(
        session: Session,
        tickets: list[KitchenTicket],
    ) -> list[KitchenTicketDetailResponse]:
        """Hydrate tickets with items and routes using batch queries."""
        ticket_ids = [t.id for t in tickets]

        # Batch query all items for these tickets
        items_query = (
            select(KitchenTicketItem)
            .where(KitchenTicketItem.ticket_id.in_(ticket_ids))
            .order_by(KitchenTicketItem.created_at.asc())
        )
        all_items = list(session.exec(items_query).all())
        item_ids = [item.id for item in all_items]

        # Batch query all routes for these items
        routes_by_item: dict[UUID, list[KitchenTicketItemRouteResponse]] = defaultdict(list)
        if item_ids:
            routes_query = (
                select(KitchenTicketItemRoute)
                .where(KitchenTicketItemRoute.ticket_item_id.in_(item_ids))
                .order_by(KitchenTicketItemRoute.created_at.asc())
            )
            for r in session.exec(routes_query).all():
                routes_by_item[r.ticket_item_id].append(
                    KitchenTicketItemRouteResponse.model_validate(r)
                )

        # Group items by ticket
        items_by_ticket: dict[UUID, list[KitchenTicketItemResponse]] = defaultdict(list)
        for item in all_items:
            item_resp = KitchenTicketItemResponse(
                id=item.id,
                ticket_id=item.ticket_id,
                source_order_item_id=item.source_order_item_id,
                menu_item_id=item.menu_item_id,
                item_name=item.item_name,
                quantity=item.quantity,
                modifiers=item.modifiers or [],
                special_instructions=item.special_instructions,
                allergens=item.allergens or [],
                course_name=item.course_name,
                status=item.status,
                routing_status=item.routing_status,
                routes=routes_by_item.get(item.id, []),
                started_at=item.started_at,
                ready_at=item.ready_at,
                cancelled_at=item.cancelled_at,
            )
            items_by_ticket[item.ticket_id].append(item_resp)

        # Assemble full ticket responses
        result: list[KitchenTicketDetailResponse] = []
        for t in tickets:
            result.append(
                KitchenTicketDetailResponse(
                    id=t.id,
                    restaurant_id=t.restaurant_id,
                    source_order_id=t.source_order_id,
                    order_number=t.order_number,
                    order_type=t.order_type,
                    dining_option=t.dining_option,
                    table_label=t.table_label,
                    customer_display_name=t.customer_display_name,
                    special_instructions=t.special_instructions,
                    status=t.status,
                    priority=t.priority,
                    received_at=t.received_at,
                    started_at=t.started_at,
                    ready_at=t.ready_at,
                    cancelled_at=t.cancelled_at,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                    items=items_by_ticket.get(t.id, []),
                )
            )

        return result

   
    # Ticket & Route Lifecycle Mutations


    @staticmethod
    def update_route_status(
        session: Session,
        ticket_id: UUID,
        route_id: UUID,
        new_status: KitchenItemStatus,
        restaurant_id: UUID,
        actor_employee_id: UUID | None = None,
    ) -> dict:
        """
        Update preparation status for a specific station route of an item.
        Validates state transitions, records audit events, cascades to parent item and ticket,
        and returns affected station IDs for real-time KDS broadcasts.
        """
        route = session.exec(
            select(KitchenTicketItemRoute)
            .join(KitchenTicketItem, KitchenTicketItem.id == KitchenTicketItemRoute.ticket_item_id)
            .join(KitchenTicket, KitchenTicket.id == KitchenTicketItem.ticket_id)
            .where(
                KitchenTicketItemRoute.id == route_id,
                KitchenTicketItem.ticket_id == ticket_id,
                KitchenTicket.restaurant_id == restaurant_id,
            )
        ).first()

        if route is None:
            raise NotFoundError(f"Route {route_id} not found for ticket {ticket_id}")

        current_status = route.status

        # Idempotent return if already in the target status
        if current_status == new_status:
            return {
                "route_id": str(route.id),
                "station_id": str(route.station_id),
                "ticket_id": str(ticket_id),
                "status": new_status.value,
                "ticket_status": None,
                "station_ids": [str(route.station_id)],
            }

        # Validate status transitions
        # Terminal: CANCELLED cannot transition to anything
        if current_status == KitchenItemStatus.CANCELLED:
            raise InvalidStateTransitionError("Cannot update a cancelled item route")

        # Valid transitions from QUEUED
        if current_status == KitchenItemStatus.QUEUED:
            if new_status not in [KitchenItemStatus.IN_PROGRESS, KitchenItemStatus.READY, KitchenItemStatus.CANCELLED]:
                raise InvalidStateTransitionError(f"Invalid transition from {current_status} to {new_status}")

        # Valid transitions from IN_PROGRESS
        elif current_status == KitchenItemStatus.IN_PROGRESS:
            if new_status not in [KitchenItemStatus.READY, KitchenItemStatus.CANCELLED]:
                raise InvalidStateTransitionError(f"Invalid transition from {current_status} to {new_status}")

        # Valid transitions from READY
        elif current_status == KitchenItemStatus.READY:
            if new_status not in [KitchenItemStatus.CANCELLED]:
                raise InvalidStateTransitionError(f"Cannot revert ready route to {new_status}")

        now = utc_now()
        route.status = new_status
        if new_status == KitchenItemStatus.IN_PROGRESS and route.started_at is None:
            route.started_at = now
        elif new_status == KitchenItemStatus.READY:
            route.ready_at = now
        elif new_status == KitchenItemStatus.CANCELLED:
            route.cancelled_at = now

        session.add(route)

        # Audit event for route transition
        event_type_map = {
            KitchenItemStatus.IN_PROGRESS: KitchenEventType.ITEM_STARTED,
            KitchenItemStatus.READY: KitchenEventType.ITEM_READY,
            KitchenItemStatus.CANCELLED: KitchenEventType.ITEM_CANCELLED,
        }
        event_type = event_type_map.get(new_status)
        if event_type:
            session.add(
                KitchenEvent(
                    restaurant_id=restaurant_id,
                    ticket_id=ticket_id,
                    ticket_item_id=route.ticket_item_id,
                    event_type=event_type,
                    actor_employee_id=actor_employee_id,
                    payload={
                        "route_id": str(route.id),
                        "station_id": str(route.station_id),
                        "station_name": route.station_name,
                        "status": new_status.value,
                    },
                )
            )

        # Cascade to parent KitchenTicketItem
        parent_item = session.exec(
            select(KitchenTicketItem).where(KitchenTicketItem.id == route.ticket_item_id)
        ).first()

        all_routes_for_item = list(
            session.exec(
                select(KitchenTicketItemRoute).where(
                    KitchenTicketItemRoute.ticket_item_id == route.ticket_item_id
                )
            ).all()
        )

        if parent_item:
            if new_status == KitchenItemStatus.IN_PROGRESS:
                if parent_item.status == KitchenItemStatus.QUEUED:
                    parent_item.status = KitchenItemStatus.IN_PROGRESS
                    parent_item.started_at = now
                    session.add(parent_item)

            elif new_status == KitchenItemStatus.READY:
                # If all routes for this item are now READY or CANCELLED, mark item READY
                if all(r.status in [KitchenItemStatus.READY, KitchenItemStatus.CANCELLED] for r in all_routes_for_item):
                    parent_item.status = KitchenItemStatus.READY
                    parent_item.ready_at = now
                    session.add(parent_item)

            elif new_status == KitchenItemStatus.CANCELLED:
                # If all routes for this item are CANCELLED, mark item CANCELLED
                if all(r.status == KitchenItemStatus.CANCELLED for r in all_routes_for_item):
                    parent_item.status = KitchenItemStatus.CANCELLED
                    parent_item.cancelled_at = now
                    session.add(parent_item)

        # Cascade to KitchenTicket
        ticket = session.exec(
            select(KitchenTicket).where(KitchenTicket.id == ticket_id)
        ).first()

        if ticket:
            all_ticket_items = list(
                session.exec(
                    select(KitchenTicketItem).where(KitchenTicketItem.ticket_id == ticket_id)
                ).all()
            )

            if new_status == KitchenItemStatus.IN_PROGRESS and ticket.status == KitchenTicketStatus.OPEN:
                ticket.status = KitchenTicketStatus.IN_PROGRESS
                ticket.started_at = now
                session.add(ticket)

            # Check if all items on ticket are now READY (or CANCELLED)
            if all(it.status in [KitchenItemStatus.READY, KitchenItemStatus.CANCELLED] for it in all_ticket_items):
                if any(it.status == KitchenItemStatus.READY for it in all_ticket_items):
                    ticket.status = KitchenTicketStatus.READY
                    ticket.ready_at = now
                    session.add(ticket)
                    session.add(
                        KitchenEvent(
                            restaurant_id=restaurant_id,
                            ticket_id=ticket_id,
                            event_type=KitchenEventType.TICKET_READY,
                            actor_employee_id=actor_employee_id,
                            payload={"ticket_id": str(ticket_id)},
                        )
                    )

        # Collect all station IDs associated with this ticket for notification
        all_ticket_routes = session.exec(
            select(KitchenTicketItemRoute.station_id)
            .join(KitchenTicketItem, KitchenTicketItem.id == KitchenTicketItemRoute.ticket_item_id)
            .where(KitchenTicketItem.ticket_id == ticket_id)
        ).all()
        station_ids = list({str(sid) for sid in all_ticket_routes})

        session.commit()

        return {
            "route_id": str(route.id),
            "station_id": str(route.station_id),
            "ticket_id": str(ticket_id),
            "status": new_status.value,
            "ticket_status": ticket.status.value if ticket else None,
            "station_ids": station_ids,
        }

    @staticmethod
    def update_ticket_status(
        session: Session,
        ticket_id: UUID,
        new_status: KitchenTicketStatus,
        restaurant_id: UUID,
        actor_employee_id: UUID | None = None,
    ) -> dict:
        """Update entire ticket status with business validation and cascading to items/routes."""
        ticket = session.exec(
            select(KitchenTicket).where(
                KitchenTicket.id == ticket_id,
                KitchenTicket.restaurant_id == restaurant_id,
            )
        ).first()

        if ticket is None:
            raise NotFoundError(f"Kitchen ticket {ticket_id} not found")

        current_status = ticket.status
        if current_status == new_status:
            return {
                "ticket_id": str(ticket.id),
                "status": ticket.status.value,
                "station_ids": [],
            }

        # Terminal state
        if current_status == KitchenTicketStatus.CANCELLED:
            raise InvalidStateTransitionError("Cannot update a cancelled ticket")

        if current_status == KitchenTicketStatus.READY and new_status != KitchenTicketStatus.CANCELLED:
            raise InvalidStateTransitionError(f"Cannot transition ticket from READY to {new_status}")

        now = utc_now()
        ticket.status = new_status

        # Collect station IDs for broadcast
        all_ticket_routes = session.exec(
            select(KitchenTicketItemRoute)
            .join(KitchenTicketItem, KitchenTicketItem.id == KitchenTicketItemRoute.ticket_item_id)
            .where(KitchenTicketItem.ticket_id == ticket_id)
        ).all()
        station_ids = list({str(r.station_id) for r in all_ticket_routes})

        all_ticket_items = session.exec(
            select(KitchenTicketItem).where(KitchenTicketItem.ticket_id == ticket_id)
        ).all()

        if new_status == KitchenTicketStatus.IN_PROGRESS:
            if ticket.started_at is None:
                ticket.started_at = now
            for item in all_ticket_items:
                if item.status == KitchenItemStatus.QUEUED:
                    item.status = KitchenItemStatus.IN_PROGRESS
                    item.started_at = now
                    session.add(item)
            for route in all_ticket_routes:
                if route.status == KitchenItemStatus.QUEUED:
                    route.status = KitchenItemStatus.IN_PROGRESS
                    route.started_at = now
                    session.add(route)

        elif new_status == KitchenTicketStatus.READY:
            ticket.ready_at = now
            for item in all_ticket_items:
                if item.status != KitchenItemStatus.CANCELLED:
                    item.status = KitchenItemStatus.READY
                    item.ready_at = now
                    session.add(item)
            for route in all_ticket_routes:
                if route.status != KitchenItemStatus.CANCELLED:
                    route.status = KitchenItemStatus.READY
                    route.ready_at = now
                    session.add(route)
            session.add(
                KitchenEvent(
                    restaurant_id=restaurant_id,
                    ticket_id=ticket.id,
                    event_type=KitchenEventType.TICKET_READY,
                    actor_employee_id=actor_employee_id,
                    payload={"ticket_id": str(ticket.id)},
                )
            )

        elif new_status == KitchenTicketStatus.CANCELLED:
            ticket.cancelled_at = now
            for item in all_ticket_items:
                item.status = KitchenItemStatus.CANCELLED
                item.cancelled_at = now
                session.add(item)
            for route in all_ticket_routes:
                route.status = KitchenItemStatus.CANCELLED
                route.cancelled_at = now
                session.add(route)
            session.add(
                KitchenEvent(
                    restaurant_id=restaurant_id,
                    ticket_id=ticket.id,
                    event_type=KitchenEventType.TICKET_CANCELLED,
                    actor_employee_id=actor_employee_id,
                    payload={"ticket_id": str(ticket.id)},
                )
            )

        session.add(ticket)
        session.commit()

        return {
            "ticket_id": str(ticket.id),
            "status": ticket.status.value,
            "station_ids": station_ids,
        }
