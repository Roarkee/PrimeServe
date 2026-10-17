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

from ..schemas.pos_schema import MenuCreate,MenuItemUpdate
from ..exceptions import CategoryAlreadyExistsError,CategoryNotFoundError,BusinessValidationError
import json

import time

from collections import OrderedDict
from sqlalchemy import and_


logger = logging.getLogger(__name__)
class MenuService:  


    @staticmethod
    def get_menu(session: Session,restaurant_id: UUID) -> MenuResponse:

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

        start = time.perf_counter()
        result = session.exec(statement)
        execute_ms = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        rows = result.all()
        fetch_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "MENU_QUERY_TIMING %s",
            json.dumps({
                "execute_ms": round(execute_ms, 2),
                "fetch_ms": round(fetch_ms, 2),
                "total_db_ms": round(execute_ms + fetch_ms, 2),
                "row_count": len(rows),
            }),
        )

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





    @staticmethod
    def update_menu_item(
        pk: UUID,
        data: MenuItemUpdate,
        session: Session,
        restaurant_id: UUID,
    ) -> MenuItem:

        menu_item = session.exec(
            select(MenuItem).where(
                MenuItem.id == pk,
                MenuItem.restaurant_id == restaurant_id,
            )
        ).first()

        if menu_item is None:
            raise ValueError("No such menu item exists")

        updates = data.model_dump(
            exclude_unset=True,
            exclude={"option_groups"},
        )

        try:
            # Update ordinary menu-item fields.
            for field, value in updates.items():
                if field in {"name", "price", "status", "display_order"} and value is None:
                    raise ValueError(f"{field} cannot be null")

            if "category_id" in updates and updates["category_id"] is not None:
                category = session.exec(
                    select(Category).where(
                        Category.id == updates["category_id"],
                        Category.restaurant_id == restaurant_id,
                    )
                ).first()

                if category is None:
                    raise ValueError("Category does not exist")

            for field, value in updates.items():
                setattr(menu_item, field, value)

            # If option_groups was omitted, leave all associations unchanged.
            if "option_groups" not in data.model_fields_set:
                session.add(menu_item)
                session.commit()
                session.refresh(menu_item)
                return menu_item

            requested_groups = data.option_groups or []
            requested_group_ids = set()

            # Load the current menu item's group associations.
            existing_links = session.exec(
                select(MenuItemOptionGroup).where(
                    MenuItemOptionGroup.menu_item_id == pk
                )
            ).all()

            # Create or update the requested groups.
            for group_data in requested_groups:

                group_fields = group_data.model_dump(
                    exclude_unset=True,
                    exclude={"id", "options"},
                )

                if group_data.id is not None:
                    # Existing group: it must belong to this restaurant.
                    group = session.exec(
                        select(OptionGroup).where(
                            OptionGroup.id == group_data.id,
                            OptionGroup.restaurant_id == restaurant_id,
                        )
                    ).first()

                    if group is None:
                        raise ValueError(
                            "Option group does not exist for this restaurant"
                        )

                    # Updating these fields changes the shared group globally.
                    for field, value in group_fields.items():
                        if field in {
                            "name",
                            "is_required",
                            "min_selections",
                            "max_selections",
                            "display_order",
                            "is_active",
                        } and value is None:
                            raise ValueError(f"{field} cannot be null")

                        setattr(group, field, value)

                    session.add(group)

                else:
                    # New group: a name is required.
                    if not group_data.name:
                        raise ValueError(
                            "A name is required when creating an option group"
                        )

                    group = OptionGroup(
                        restaurant_id=restaurant_id,
                        **group_fields,
                    )
                    session.add(group)
                    session.flush()

                group_id = group.id
                requested_group_ids.add(group_id)

                # Attach the group to this menu item if not already attached.
                link = next(
                    (
                        item for item in existing_links
                        if item.option_group_id == group_id
                    ),
                    None,
                )

                if link is None:
                    link = MenuItemOptionGroup(
                        menu_item_id=pk,
                        option_group_id=group_id,
                        display_order=(
                            group_data.display_order
                            if group_data.display_order is not None
                            else 0
                        ),
                    )
                    session.add(link)
                elif group_data.display_order is not None:
                    # This changes the order for this menu item only.
                    link.display_order = group_data.display_order
                    session.add(link)

                # No options field means leave the group's options unchanged.
                if group_data.options is None:
                    continue

                for option_data in group_data.options:
                    option_fields = option_data.model_dump(
                        exclude_unset=True,
                        exclude={"id"},
                    )

                    if option_data.id is not None:
                        option = session.exec(
                            select(Option).where(
                                Option.id == option_data.id,
                                Option.option_group_id == group_id,
                            )
                        ).first()

                        if option is None:
                            raise ValueError(
                                "Option does not belong to the specified group"
                            )

                        for field, value in option_fields.items():
                            if field in {"name", "additional_price", "display_order", "is_active"} and value is None:
                                raise ValueError(f"{field} cannot be null")

                            setattr(option, field, value)

                        session.add(option)

                    else:
                        if not option_data.name:
                            raise ValueError(
                                "A name is required when creating an option"
                            )

                        option = Option(
                            option_group_id=group_id,
                            **option_fields,
                        )
                        session.add(option)

            # The provided list represents the groups attached to this item.
            # Remove associations omitted from the list; do not delete groups.
            for link in existing_links:
                if link.option_group_id not in requested_group_ids:
                    session.delete(link)

            session.add(menu_item)
            session.commit()
            session.refresh(menu_item)

            return menu_item

        except Exception:
            session.rollback()
            raise



    
    @staticmethod
    def delete_menu(pk,session:Session, restaurant_id:UUID):
        menu_item = session.exec(
                    select(MenuItem).where(
                        MenuItem.id == pk,
                        MenuItem.restaurant_id == restaurant_id
                    )
                ).first()
        
        if menu_item is None:
            raise ValueError("No such menu item exists")
        
        session.delete(menu_item)
        session.commit()
        return menu_item
       




    @staticmethod
    def get_all_menus(session:Session, restaurant_id:UUID):
        menu_items = session.exec(
                            select(MenuItem).where( 
                                MenuItem.restaurant_id == restaurant_id
                            )
                        ).all()
        return menu_items