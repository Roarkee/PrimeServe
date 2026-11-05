import logging
from collections import defaultdict
from uuid import UUID
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import Session, select

from ..models import (
    KitchenTicket,
    KitchenTicketItem,
    KitchenTicketItemRoute,
    KitchenEvent,
    KitchenEventType,
    KitchenItemStatus,
    KitchenRoutingStatus,
    KitchenTicketStatus,
    MenuItemRouting,
    PrepStation,
    ProcessedEvent,
)
from ..schema.internal_schema import KitchenOrderEvent

logger = logging.getLogger(__name__)


class OrderEventService:

    @staticmethod
    def receive_order_created(
        session: Session,
        event: KitchenOrderEvent,
    ) -> dict:
        """
        Process an order.created event from the Orders microservice idempotently.
        Creates KitchenTicket, KitchenTicketItems, KitchenTicketItemRoutes, and KitchenEvents
        in a single atomic transaction.
        """
        if event.event_type != "order.created":
            raise ValueError(f"Unsupported event type: {event.event_type}")

        order = event.payload.order

        if not order.items:
            raise ValueError("Order must contain at least one item to create a kitchen ticket")

        try:
            # 1. Atomically claim the event ID via ON CONFLICT DO NOTHING.
            # A concurrent duplicate delivery cannot also claim this record.
            statement = (
                pg_insert(ProcessedEvent)
                .values(
                    id=event.id,
                    event_type=event.event_type,
                    aggregate_id=event.aggregate_id,
                    aggregate_version=event.aggregate_version,
                )
                .on_conflict_do_nothing(
                    index_elements=[ProcessedEvent.id]
                )
                .returning(ProcessedEvent.id)
            )

            inserted_event_id = session.exec(statement).scalar_one_or_none()

            # If this event ID was already processed, handle idempotently.
            if inserted_event_id is None:
                existing_ticket = session.exec(
                    select(KitchenTicket).where(
                        KitchenTicket.source_order_id == order.id
                    )
                ).first()

                return {
                    "status": "duplicate",
                    "event_id": str(event.id),
                    "ticket_id": str(existing_ticket.id) if existing_ticket else None,
                    "station_ids": [],
                }

            # 2. Check if a ticket already exists for this source order under a different event ID.
            existing_ticket = session.exec(
                select(KitchenTicket).where(
                    KitchenTicket.source_order_id == order.id
                )
            ).first()

            if existing_ticket is not None:
                raise ValueError(
                    f"Kitchen ticket already exists for order {order.id}"
                )

            # 3. Create the KitchenTicket record.
            ticket = KitchenTicket(
                restaurant_id=order.restaurant_id,
                source_order_id=order.id,
                order_number=str(order.order_number),
                order_type=order.order_type,
                special_instructions=order.notes,
                status=KitchenTicketStatus.OPEN,
                source_order_version=order.revision,
            )
            session.add(ticket)

            # 4. Batch fetch all active routing configurations for all items in this order.
            menu_item_ids = list({item.menu_item_id for item in order.items if item.menu_item_id})
            routes_by_item: dict[UUID, list[tuple[MenuItemRouting, PrepStation]]] = defaultdict(list)

            if menu_item_ids:
                routing_statement = (
                    select(MenuItemRouting, PrepStation)
                    .join(
                        PrepStation,
                        PrepStation.id == MenuItemRouting.station_id,
                    )
                    .where(
                        MenuItemRouting.restaurant_id == order.restaurant_id,
                        MenuItemRouting.menu_item_id.in_(menu_item_ids),
                        MenuItemRouting.is_active.is_(True),
                        PrepStation.restaurant_id == order.restaurant_id,
                        PrepStation.is_active.is_(True),
                    )
                )
                for routing, station in session.exec(routing_statement).all():
                    routes_by_item[routing.menu_item_id].append((routing, station))

            # 5. Create KitchenTicketItems first and flush so FK constraints on ticket_items are satisfied
            created_items_with_order: list[tuple[KitchenTicketItem, list[tuple[MenuItemRouting, PrepStation]]]] = []
            for order_item in order.items:
                matching_routes = routes_by_item.get(order_item.menu_item_id, [])
                routing_status = (
                    KitchenRoutingStatus.ROUTED
                    if matching_routes
                    else KitchenRoutingStatus.UNROUTED
                )

                ticket_item = KitchenTicketItem(
                    ticket_id=ticket.id,
                    source_order_item_id=order_item.id,
                    menu_item_id=order_item.menu_item_id,
                    item_name=order_item.name,
                    quantity=order_item.quantity,
                    modifiers=[
                        option.model_dump(mode="json")
                        for option in order_item.options
                    ],
                    special_instructions=order_item.notes,
                    status=KitchenItemStatus.QUEUED,
                    routing_status=routing_status,
                )
                session.add(ticket_item)
                created_items_with_order.append((ticket_item, matching_routes))

            # Flush to persist ticket and items so child routes and events can reference them
            session.flush()

            unrouted_items = 0
            routed_items = 0
            station_ids: set[str] = set()

            # 6. Create routes and item-level events
            for ticket_item, matching_routes in created_items_with_order:
                if matching_routes:
                    for _, station in matching_routes:
                        station_ids.add(str(station.id))
                        session.add(
                            KitchenTicketItemRoute(
                                restaurant_id=order.restaurant_id,
                                ticket_item_id=ticket_item.id,
                                station_id=station.id,
                                station_name=station.name,
                                status=KitchenItemStatus.QUEUED,
                            )
                        )
                    routed_items += 1
                else:
                    unrouted_items += 1
                    session.add(
                        KitchenEvent(
                            restaurant_id=order.restaurant_id,
                            ticket_id=ticket.id,
                            ticket_item_id=ticket_item.id,
                            event_type=KitchenEventType.ITEM_UNROUTED,
                            payload={
                                "menu_item_id": str(ticket_item.menu_item_id),
                                "item_name": ticket_item.item_name,
                                "reason": "No active station routing configured",
                            },
                        )
                    )

            # 7. Record the TICKET_CREATED event.
            session.add(
                KitchenEvent(
                    restaurant_id=order.restaurant_id,
                    ticket_id=ticket.id,
                    event_type=KitchenEventType.TICKET_CREATED,
                    payload={
                        "source_order_id": str(order.id),
                        "order_number": order.order_number,
                        "item_count": len(order.items),
                        "routed_items": routed_items,
                        "unrouted_items": unrouted_items,
                    },
                )
            )

            # 8. Commit the entire transaction atomically.
            session.commit()

            return {
                "status": "processed",
                "event_id": str(event.id),
                "ticket_id": str(ticket.id),
                "routed_items": routed_items,
                "unrouted_items": unrouted_items,
                "station_ids": list(station_ids),
            }

        except Exception as exc:
            session.rollback()
            logger.exception("Failed processing order.created event %s: %s", event.id, exc)
            raise
