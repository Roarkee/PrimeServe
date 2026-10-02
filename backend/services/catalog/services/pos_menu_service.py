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
from ..schema import (
    CategoryMenuResponse,
    MenuItemMenuResponse,
    MenuOptionGroupResponse,
    MenuOptionResponse,
    MenuResponse,
)


class MenuReadService:

    @staticmethod
    def get_menu(
        session: Session,
        restaurant_id: UUID
    ) -> MenuResponse:

        categories = session.exec(
            select(Category)
            .where(
                Category.restaurant_id == restaurant_id,
                Category.is_active == True
            )
            .order_by(Category.display_order)
        ).all()

        menu_items = session.exec(
            select(MenuItem)
            .where(
                MenuItem.restaurant_id == restaurant_id,
                MenuItem.status == MenuItemStatus.ACTIVE
            )
            .order_by(MenuItem.display_order)
        ).all()

        relationships = session.exec(
            select(MenuItemOptionGroup)
            .join(
                MenuItem,
                MenuItemOptionGroup.menu_item_id == MenuItem.id
            )
            .join(
                OptionGroup,
                MenuItemOptionGroup.option_group_id == OptionGroup.id
            )
            .where(
                MenuItem.restaurant_id == restaurant_id,
                OptionGroup.is_active == True
            )
            .order_by(MenuItemOptionGroup.display_order)
        ).all()

        option_groups = session.exec(
            select(OptionGroup)
            .where(
                OptionGroup.restaurant_id == restaurant_id,
                OptionGroup.is_active == True
            )
            .order_by(OptionGroup.display_order)
        ).all()

        options = session.exec(
            select(Option)
            .join(
                OptionGroup,
                Option.option_group_id == OptionGroup.id
            )
            .where(
                OptionGroup.restaurant_id == restaurant_id,
                Option.is_active == True
            )
            .order_by(Option.display_order)
        ).all()

        items_by_category: dict[UUID, list[MenuItem]] = {}

        for item in menu_items:
            if item.category_id is not None:
                items_by_category.setdefault(
                    item.category_id,
                    []
                ).append(item)

        groups_by_item: dict[UUID, list[MenuItemOptionGroup]] = {}

        for relationship in relationships:
            groups_by_item.setdefault(
                relationship.menu_item_id,
                []
            ).append(relationship)

        option_groups_by_id = {
            group.id: group
            for group in option_groups
        }

        options_by_group: dict[UUID, list[Option]] = {}

        for option in options:
            options_by_group.setdefault(
                option.option_group_id,
                []
            ).append(option)

        category_responses = []

        for category in categories:

            item_responses = []

            for item in items_by_category.get(category.id, []):

                group_responses = []

                for relationship in groups_by_item.get(item.id, []):

                    group = option_groups_by_id.get(
                        relationship.option_group_id
                    )

                    if group is None:
                        continue

                    option_responses = [
                        MenuOptionResponse(
                            id=option.id,
                            name=option.name,
                            additional_price=option.additional_price,
                            display_order=option.display_order
                        )
                        for option in options_by_group.get(
                            group.id,
                            []
                        )
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

        return MenuResponse(
            categories=category_responses
        )