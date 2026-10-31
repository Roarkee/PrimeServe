
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import Session,select

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


class OrderEventService:

    @staticmethod
    def receive_order_created(
        session: Session,
        event: KitchenOrderEvent,
    ) -> dict:
        if event.event_type != "order.created":
            raise ValueError(f"Unsupported event type: {event.event_type}")

        order = event.payload.order

        try:
            # Atomically claim the event ID.
            # A concurrent duplicate cannot also insert this record.
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

            if inserted_event_id is None:
                session.rollback()
                return {
                    "status": "duplicate",
                    "event_id": str(event.id),
                }

            # A second event ID for an order that already has a ticket
            # is not an ordinary duplicate. Do not silently accept it.
            existing_ticket = session.exec(
                select(KitchenTicket).where(
                    KitchenTicket.source_order_id == order.id
                )
            ).first()

            if existing_ticket is not None:
                raise ValueError(
                    f"Kitchen ticket already exists for order {order.id}"
                )

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
            session.flush()

            unrouted_items = 0
            routed_items = 0

            for order_item in order.items:
                # Find active routes whose stations are also active
                # and belong to the same restaurant.
                routing_statement = (
                    select(MenuItemRouting, PrepStation)
                    .join(
                        PrepStation,
                        PrepStation.id == MenuItemRouting.station_id,
                    )
                    .where(
                        MenuItemRouting.restaurant_id == order.restaurant_id,
                        MenuItemRouting.menu_item_id == order_item.menu_item_id,
                        MenuItemRouting.is_active.is_(True),
                        PrepStation.restaurant_id == order.restaurant_id,
                        PrepStation.is_active.is_(True),
                    )
                )

                routing_rows = session.exec(routing_statement).all()

                routing_status = (
                    KitchenRoutingStatus.ROUTED
                    if routing_rows
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
                session.flush()

                if routing_rows:
                    for routing, station in routing_rows:
                        session.add(
                            KitchenTicketItemRoute(
                                restaurant_id=order.restaurant_id,
                                ticket_item_id=ticket_item.id,
                                station_id=station.id,
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
                                "menu_item_id": str(order_item.menu_item_id),
                                "item_name": order_item.name,
                                "reason": "No active station routing configured",
                            },
                        )
                    )

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

            session.commit()

            return {
                "status": "processed",
                "event_id": str(event.id),
                "ticket_id": str(ticket.id),
                "routed_items": routed_items,
                "unrouted_items": unrouted_items,
            }

        except Exception:
            session.rollback()
            raise
