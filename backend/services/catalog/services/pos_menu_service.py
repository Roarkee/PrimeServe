import logging
from uuid import UUID

from sqlmodel import Session, select

from ..models import (
    Category,
    MenuItem,
    MenuItemOptionGroup,
    Option,
    MenuItemStatus,
    OptionGroup,
)
from ..schemas.management_schema import (
    CategoryMenuResponse,
    MenuItemMenuResponse,
    MenuOptionGroupResponse,
    MenuOptionResponse,
    MenuResponse,

)

from ..schemas.pos_schema import MenuCreate
from ..exceptions import CategoryAlreadyExistsError,CategoryNotFoundError,BusinessValidationError
import json

import time

from collections import OrderedDict
from sqlalchemy import and_


logger = logging.getLogger(__name__)


class MenuReadService:

    



    @staticmethod
    def get_menu(
        session: Session,
        restaurant_id: UUID
    ) -> MenuResponse:

        statement = (
            select(
                Category,
                MenuItem,
                MenuItemOptionGroup,
                OptionGroup,
                Option,
            )
            .select_from(Category)
            .outerjoin(
                MenuItem,
                and_(
                    MenuItem.category_id == Category.id,
                    MenuItem.restaurant_id == restaurant_id,
                    MenuItem.status == MenuItemStatus.ACTIVE,
                ),
            )
            .outerjoin(
                MenuItemOptionGroup,
                MenuItemOptionGroup.menu_item_id == MenuItem.id,
            )
            .outerjoin(
                OptionGroup,
                and_(
                    OptionGroup.id
                    == MenuItemOptionGroup.option_group_id,
                    OptionGroup.restaurant_id == restaurant_id,
                    OptionGroup.is_active.is_(True),
                ),
            )
            .outerjoin(
                Option,
                and_(
                    Option.option_group_id == OptionGroup.id,
                    Option.is_active.is_(True),
                ),
            )
            .where(
                Category.restaurant_id == restaurant_id,
                Category.is_active.is_(True),
            )
            .order_by(
                Category.display_order,
                MenuItem.display_order,
                MenuItemOptionGroup.display_order,
                Option.display_order,
            )
        )

        rows = session.exec(statement).all()

        # Ordered dictionaries preserve the database display order.
        categories_by_id = OrderedDict()

        for category, item, relationship, group, option in rows:

            if category.id not in categories_by_id:
                categories_by_id[category.id] = {
                    "category": category,
                    "items": OrderedDict(),
                }

            # Empty categories are retained.
            if item is None:
                continue

            items = categories_by_id[category.id]["items"]

            if item.id not in items:
                items[item.id] = {
                    "item": item,
                    "groups": OrderedDict(),
                }

            # Items without option groups are retained.
            if relationship is None or group is None:
                continue

            groups = items[item.id]["groups"]

            if group.id not in groups:
                groups[group.id] = {
                    "group": group,
                    "display_order": relationship.display_order,
                    "options": OrderedDict(),
                }

            # Groups without active options are retained.
            if option is not None:
                groups[group.id]["options"].setdefault(
                    option.id,
                    option,
                )

        category_responses = []

        for category_data in categories_by_id.values():
            category = category_data["category"]
            item_responses = []

            for item_data in category_data["items"].values():
                item = item_data["item"]
                group_responses = []

                for group_data in item_data["groups"].values():
                    group = group_data["group"]

                    option_responses = [
                        MenuOptionResponse(
                            id=option.id,
                            name=option.name,
                            additional_price=option.additional_price,
                            display_order=option.display_order,
                        )
                        for option in group_data["options"].values()
                    ]

                    group_responses.append(
                        MenuOptionGroupResponse(
                            id=group.id,
                            name=group.name,
                            description=group.description,
                            is_required=group.is_required,
                            min_selections=group.min_selections,
                            max_selections=group.max_selections,
                            display_order=group_data["display_order"],
                            options=option_responses,
                        )
                    )

                item_responses.append(
                    MenuItemMenuResponse(
                        id=item.id,
                        category_id=item.category_id,
                        name=item.name,
                        description=item.description,
                        sku=item.sku,
                        price=item.price,
                        status=item.status,
                        image_path=item.image_path,
                        display_order=item.display_order,
                        option_groups=group_responses,
                    )
                )

            category_responses.append(
                CategoryMenuResponse(
                    id=category.id,
                    name=category.name,
                    description=category.description,
                    display_order=category.display_order,
                    items=item_responses,
                )
            )

        return MenuResponse(categories=category_responses)

    @staticmethod
    def get_menu(session: Session, restaurant_id: UUID) -> MenuResponse:
        request_start = time.perf_counter()
        timings = {}

        # 1. Fetch categories
        start = time.perf_counter()
        categories = session.exec(
            select(Category)
            .where(
                Category.restaurant_id == restaurant_id,
                Category.is_active == True
            )
            .order_by(Category.display_order)
        ).all()
        timings["categories_ms"] = round((time.perf_counter() - start) * 1000, 2)

        # 2. Fetch active menu items
        start = time.perf_counter()
        menu_items = session.exec(
            select(MenuItem)
            .where(
                MenuItem.restaurant_id == restaurant_id,
                MenuItem.status == MenuItemStatus.ACTIVE
            )
            .order_by(MenuItem.display_order)
        ).all()
        timings["menu_items_ms"] = round((time.perf_counter() - start) * 1000, 2)

        # 3. Fetch menu-item/option-group relationships
        start = time.perf_counter()
        relationships = session.exec(
            select(MenuItemOptionGroup)
            .join(MenuItem, MenuItemOptionGroup.menu_item_id == MenuItem.id)
            .join(OptionGroup, MenuItemOptionGroup.option_group_id == OptionGroup.id)
            .where(
                MenuItem.restaurant_id == restaurant_id,
                OptionGroup.is_active == True
            )
            .order_by(MenuItemOptionGroup.display_order)
        ).all()
        timings["relationships_ms"] = round((time.perf_counter() - start) * 1000, 2)

        # 4. Fetch active option groups
        start = time.perf_counter()
        option_groups = session.exec(
            select(OptionGroup)
            .where(
                OptionGroup.restaurant_id == restaurant_id,
                OptionGroup.is_active == True
            )
            .order_by(OptionGroup.display_order)
        ).all()
        timings["option_groups_ms"] = round((time.perf_counter() - start) * 1000, 2)

        # 5. Fetch active options
        start = time.perf_counter()
        options = session.exec(
            select(Option)
            .join(OptionGroup, Option.option_group_id == OptionGroup.id)
            .where(
                OptionGroup.restaurant_id == restaurant_id,
                Option.is_active == True
            )
            .order_by(Option.display_order)
        ).all()
        timings["options_ms"] = round((time.perf_counter() - start) * 1000, 2)

        timings["db_total_ms"] = round(sum((
            timings["categories_ms"],
            timings["menu_items_ms"],
            timings["relationships_ms"],
            timings["option_groups_ms"],
            timings["options_ms"],
        )), 2)

        # 6. Build lookup dictionaries
        assembly_start = time.perf_counter()

        items_by_category: dict[UUID, list[MenuItem]] = {}
        for item in menu_items:
            if item.category_id is not None:
                items_by_category.setdefault(item.category_id, []).append(item)

        groups_by_item: dict[UUID, list[MenuItemOptionGroup]] = {}
        for relationship in relationships:
            groups_by_item.setdefault(relationship.menu_item_id, []).append(relationship)

        option_groups_by_id = {group.id: group for group in option_groups}

        options_by_group: dict[UUID, list[Option]] = {}
        for option in options:
            options_by_group.setdefault(option.option_group_id, []).append(option)

        # 7. Build nested response
        category_responses = []

        for category in categories:
            item_responses = []

            for item in items_by_category.get(category.id, []):
                group_responses = []

                for relationship in groups_by_item.get(item.id, []):
                    group = option_groups_by_id.get(relationship.option_group_id)

                    if group is None:
                        continue

                    option_responses = [
                        MenuOptionResponse(
                            id=option.id,
                            name=option.name,
                            additional_price=option.additional_price,
                            display_order=option.display_order
                        )
                        for option in options_by_group.get(group.id, [])
                    ]

                    group_responses.append(
                        MenuOptionGroupResponse(
                            id=group.id,
                            name=group.name,
                            description=group.description,
                            is_required=group.is_required,
                            min_selections=group.min_selections,
                            max_selections=group.max_selections,
                            display_order=relationship.display_order,
                            options=option_responses
                        )
                    )

                item_responses.append(
                    MenuItemMenuResponse(
                        id=item.id,
                        category_id=item.category_id,
                        name=item.name,
                        description=item.description,
                        sku=item.sku,
                        price=item.price,
                        status=item.status,
                        image_path=item.image_path,
                        display_order=item.display_order,
                        option_groups=group_responses
                    )
                )

            category_responses.append(
                CategoryMenuResponse(
                    id=category.id,
                    name=category.name,
                    description=category.description,
                    display_order=category.display_order,
                    items=item_responses
                )
            )

        timings["assembly_ms"] = round((time.perf_counter() - assembly_start) * 1000, 2)

        response = MenuResponse(categories=category_responses)

        timings["menu_total_ms"] = round((time.perf_counter() - request_start) * 1000, 2)
        timings["category_count"] = len(categories)
        timings["menu_item_count"] = len(menu_items)
        timings["relationship_count"] = len(relationships)
        timings["option_group_count"] = len(option_groups)
        timings["option_count"] = len(options)

        logger.info("MENU_TIMING %s", json.dumps(timings))

        return response




    @staticmethod
    def create_menu(session: Session,data: MenuCreate,restaurant_id: UUID,):
        if data.category_id and data.category:
            raise BusinessValidationError("Provide either category_id or category, not both.")

        try:

            if data.category_id:

                category = session.exec(
                    select(Category).where(
                        Category.id == data.category_id,
                        Category.restaurant_id == restaurant_id,
                    )
                ).first()

                if not category:
                    raise CategoryNotFoundError(
                        "This category doesn't exist."
                    )

            elif data.category:
                category = Category(
                    restaurant_id=restaurant_id,
                    name=data.category.name,
                    description=data.category.description,
                    display_order=data.category.display_order,
                )

                session.add(category)
                session.flush()

            else:
                raise BusinessValidationError("You must provide either category_id or category.")

            menu_data = data.menu_item

            menu_item = MenuItem(
                restaurant_id=restaurant_id,
                category_id=category.id,
                name=menu_data.name,
                description=menu_data.description,
                sku=menu_data.sku,
                price=menu_data.price,
                status=menu_data.status,
                image_path=menu_data.image_path,
                display_order=menu_data.display_order,
            )

            session.add(menu_item)
            session.flush()


            created_groups = []
            for group_data in menu_data.option_groups:

                option_group = OptionGroup(
                    restaurant_id=restaurant_id,
                    name=group_data.name,
                    description=group_data.description,
                    is_required=group_data.is_required,
                    min_selections=group_data.min_selections,
                    max_selections=group_data.max_selections,
                    display_order=group_data.display_order,
                    is_active=group_data.is_active,
                )

                session.add(option_group)
                session.flush()

                relationship = MenuItemOptionGroup(
                    menu_item_id=menu_item.id,
                    option_group_id=option_group.id,
                    display_order=group_data.display_order,
                )

                session.add(relationship)

                created_options = []
               
                for option_data in group_data.options:

                    option = Option(
                        option_group_id=option_group.id,
                        name=option_data.name,
                        additional_price=option_data.additional_price,
                        display_order=option_data.display_order,
                        is_active=option_data.is_active,
                    )

                    session.add(option)
                    session.flush()
                    created_options.append(option)
                created_groups.append((option_group, created_options))

            session.commit()

            session.refresh(menu_item)

            return MenuItemMenuResponse(
                id=menu_item.id,
                category_id=menu_item.category_id,
                name=menu_item.name,
                description=menu_item.description,
                sku=menu_item.sku,
                price=menu_item.price,
                status=menu_item.status,
                image_path=menu_item.image_path,
                display_order=menu_item.display_order,
                option_groups=[
                    MenuOptionGroupResponse(
                        id=option_group.id,
                        name=option_group.name,
                        description=option_group.description,
                        is_required=option_group.is_required,
                        min_selections=option_group.min_selections,
                        max_selections=option_group.max_selections,
                        display_order=option_group.display_order,
                        options=[
                            MenuOptionResponse(
                                id=option.id,
                                name=option.name,
                                additional_price=option.additional_price,
                                display_order=option.display_order,
                            )
                            for option in options
                        ],
                    )
                    for group, options in created_groups
                ],
                    )

        except Exception:
            session.rollback()
            raise