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
from ..exceptions import CategoryAlreadyExistsError,CategoryNotFoundError,ValidationError


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



    @staticmethod
    def create_menu(session: Session,data: MenuCreate,restaurant_id: UUID,):
        if data.category_id and data.category:
            raise ValidationError("Provide either category_id or category, not both.")

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
                raise ValidationError("You must provide either category_id or category.")

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