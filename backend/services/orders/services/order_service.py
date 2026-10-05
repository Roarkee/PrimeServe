from uuid import UUID
from decimal import Decimal
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlmodel import Session, select

from ..utils import generate_order_number
from ..models import OrderStatus, Order, OrderItem, OrderItemOption
from ..schema import (
    OrderCreate,
    OrderResponse,
    OrderItemResponse,
    OrderItemOptionResponse,
    CatalogValidationRequest,
    CatalogValidationItem,
)
from ..catalog_client import validate_with_catalog


class OrderService:

    @staticmethod
    def create_order(
        session: Session,
        data: OrderCreate,
        restaurant_id: UUID,
    ):

        if not data.items:
            raise ValueError("Order must contain at least one item.")

        catalog_request = CatalogValidationRequest(
            restaurant_id=restaurant_id,
            items=[
                CatalogValidationItem(
                    menu_item_id=item.menu_item_id,
                    quantity=item.quantity,
                    option_ids=item.option_ids,
                )
                for item in data.items
            ],
        )

        validated_menu = validate_with_catalog(catalog_request)

        subtotal = Decimal("0.00")

        for item in validated_menu.items:
            options_total = sum(
                (
                    option.additional_price
                    for option in item.options
                ),
                Decimal("0.00"),
            )

            item_subtotal = (
                item.price + options_total
            ) * item.quantity

            subtotal += item_subtotal

        discount = Decimal("0.00")
        tax = Decimal("0.00")
        total = subtotal - discount + tax

        counter_date = datetime.now(
            ZoneInfo("Africa/Accra")
        ).date()

        try:
            order_number = generate_order_number(
                session=session,
                restaurant_id=restaurant_id,
                counter_date=counter_date,
            )

            order = Order(
                restaurant_id=restaurant_id,
                order_number=order_number,
                order_type=data.order_type,
                status=OrderStatus.PENDING,
                subtotal=subtotal,
                discount=discount,
                tax=tax,
                total=total,
                notes=data.notes,
            )

            session.add(order)
            session.flush()

            for request_item, validated_item in zip(
                data.items,
                validated_menu.items,
            ):
                options_total = sum(
                    (
                        option.additional_price
                        for option in validated_item.options
                    ),
                    Decimal("0.00"),
                )

                item_subtotal = (
                    validated_item.price + options_total
                ) * validated_item.quantity

                order_item = OrderItem(
                    order_id=order.id,
                    menu_item_id=validated_item.menu_item_id,
                    name=validated_item.name,
                    unit_price=validated_item.price,
                    quantity=validated_item.quantity,
                    subtotal=item_subtotal,
                    notes=request_item.notes,
                )

                session.add(order_item)
                session.flush()

                for option in validated_item.options:
                    order_item_option = OrderItemOption(
                        order_item_id=order_item.id,
                        option_id=option.option_id,
                        name=option.name,
                        additional_price=option.additional_price,
                        quantity=1,
                    )

                    session.add(order_item_option)

            session.commit()
            session.refresh(order)

            items = session.exec(
                select(OrderItem).where(
                    OrderItem.order_id == order.id
                )
            ).all()

            response_items = []

            for item in items:
                options = session.exec(
                    select(OrderItemOption).where(
                        OrderItemOption.order_item_id == item.id
                    )
                ).all()

                response_items.append(
                    OrderItemResponse(
                        id=item.id,
                        menu_item_id=item.menu_item_id,
                        name=item.name,
                        unit_price=item.unit_price,
                        quantity=item.quantity,
                        subtotal=item.subtotal,
                        notes=item.notes,
                        status=item.status,
                        options=[
                            OrderItemOptionResponse(
                                id=option.id,
                                option_id=option.option_id,
                                name=option.name,
                                additional_price=option.additional_price,
                                quantity=option.quantity,
                            )
                            for option in options
                        ],
                    )
                )

            return OrderResponse(
                id=order.id,
                restaurant_id=order.restaurant_id,
                order_number=order.order_number,
                order_type=order.order_type,
                status=order.status,
                subtotal=order.subtotal,
                discount=order.discount,
                tax=order.tax,
                total=order.total,
                notes=order.notes,
                created_at=order.created_at,
                updated_at=order.updated_at,
                items=response_items,
            )

        except Exception:
            session.rollback()
            raise