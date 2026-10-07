from uuid import UUID
from decimal import Decimal
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlmodel import Session, select

from ..utils import generate_order_number
from ..models import OrderStatus, Order, OrderItem, OrderItemOption,OrderItemStatus,OrderType
from ..schema import (
    OrderCreate,
    OrderResponse,
    OrderItemResponse,
    OrderItemOptionResponse,
    CatalogValidationRequest,
    CatalogValidationItem,
    OrderListResponse,
    OrderUpdate
)
from ..catalog_client import validate_with_catalog
from .order_pricing import OrderPricingService
from math import ceil

from sqlalchemy import func
from sqlmodel import select



class OrderService:

    @staticmethod
    def create_order(session: Session,data: OrderCreate,restaurant_id: UUID,):
         

        if not data.items:
            raise ValueError("Order must contain at least one item.")

        pricing_service = OrderPricingService()

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

        calculated_items = []
        item_subtotals = []

        for request_item, validated_item in zip(
            data.items,
            validated_menu.items,
        ):
            options_total = pricing_service.calculate_options_total(
                validated_item.options
            )

            item_subtotal = pricing_service.calculate_item_subtotal(
                unit_price=validated_item.price,
                quantity=validated_item.quantity,
                options_price=options_total,
            )

            calculated_items.append(
                {
                    "request_item": request_item,
                    "validated_item": validated_item,
                    "options_total": options_total,
                    "item_subtotal": item_subtotal,
                }
            )

            item_subtotals.append(item_subtotal)

        subtotal = pricing_service.calculate_subtotal(
            item_subtotals
        )
        discount_type = "fixed"
        discount_value = Decimal("0.00")

        discount = pricing_service.calculate_discount(
            subtotal=subtotal,
            discount_type=discount_type,
            discount_value=discount_value,
        )

        tax_rate = Decimal("0.00")

        taxable_amount = subtotal - discount

        tax = pricing_service.calculate_tax(
            taxable_amount=taxable_amount,
            tax_rate=tax_rate,
        )


        total = pricing_service.calculate_total(
            subtotal=subtotal,
            discount=discount,
            tax=tax,
        )

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

            for calculated in calculated_items:

                request_item = calculated["request_item"]
                validated_item = calculated["validated_item"]
                item_subtotal = calculated["item_subtotal"]

                order_item = OrderItem(
                    order_id=order.id,
                    menu_item_id=validated_item.menu_item_id,
                    name=validated_item.name,
                    unit_price=validated_item.price,
                    quantity=validated_item.quantity,
                    subtotal=item_subtotal,
                    notes=request_item.notes,
                    status=OrderItemStatus.PENDING,
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

            item_ids = [item.id for item in items]

            item_options = []

            if item_ids:
                item_options = session.exec(
                    select(OrderItemOption).where(
                        OrderItemOption.order_item_id.in_(item_ids)
                    )
                ).all()

            options_by_item = {}

            for option in item_options:
                options_by_item.setdefault(
                    option.order_item_id,
                    []
                ).append(option)

            response_items = []

            for item in items:

                options = options_by_item.get(
                    item.id,
                    []
                )

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



    @staticmethod
    def get_orders(session: Session,restaurant_id: UUID,status: OrderStatus|None=None,order_type: OrderType|None=None,
        page: int = 1,
        page_size: int = 20,
    ):
        if page < 1:
            raise ValueError("Page must be greater than 0.")

        if page_size < 1:
            raise ValueError("Page size must be greater than 0.")

        if page_size > 100:
            raise ValueError("Page size cannot exceed 100.")

        query = select(Order).where(Order.restaurant_id == restaurant_id)

        if status is not None:
            query = query.where(Order.status == status)

        if order_type is not None:
            query = query.where(Order.order_type == order_type)

        count_query = select(func.count()).select_from(Order).where(Order.restaurant_id == restaurant_id)

        if status is not None:
            count_query = count_query.where(Order.status == status)

        if order_type is not None:
            count_query = count_query.where(Order.order_type == order_type)

        total = session.exec(count_query).one()

        offset = (page - 1) * page_size

        orders = session.exec(query.order_by(Order.created_at.desc()).offset(offset).limit(page_size)).all()

        total_pages = ceil(total / page_size) if total > 0 else 0
        
        return {
            "items": orders,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
    @staticmethod
    def get_order(pk:UUID, session:Session, restaurant_id: UUID):
        order = session.exec(
            select(Order).where(Order.id ==pk, Order.restaurant_id == restaurant_id)
        ).first()

        if not order:
            raise ValueError("there's no order existing")

        items = session.exec(
            select(OrderItem).where(OrderItem.order_id ==order.id)
        ).all()

        item_ids = [item.id for item in items]

        item_options = session.exec(
            select(OrderItemOption).where(OrderItemOption.order_item_id.in_(item_ids))
        ).all()

        options_by_item = {}

        for option in item_options:
            options_by_item.setdefault(option.order_item_id, []).append(option)

        response_items = []

        for item in items:
            item_options = options_by_item.get(item.id, [])

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
                    for option in item_options
                ],
            )
        )

        return OrderResponse(
            id=order.id,
            order_number=order.order_number,
            order_type=order.order_type,
            status=order.status,
            subtotal=order.subtotal,
            discount=order.discount,
            tax=order.tax,
            total=order.total,
            notes=order.notes,
            items=response_items,
            created_at=order.created_at,
            updated_at=order.updated_at,
    )
        

    @staticmethod  
    def update_order(pk:UUID,session:Session, restaurant_id: UUID, data:OrderUpdate):
        order = session.exec(
            select(Order).where(Order.id ==pk, Order.restaurant_id == restaurant_id)
        ).first()

        if not order:
            raise ValueError("There's no order with this ID.")

        updates = data.model_dump(exclude_unset=True)  

        for field, value in updates.items():
            setattr(order,field, value)

        session.add(order)
        session.commit()
        session.refresh(order)
        return order







