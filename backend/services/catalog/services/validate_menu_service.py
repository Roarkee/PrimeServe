from uuid import UUID

from sqlmodel import Session, select

from ..models import (
    MenuItem,
    MenuItemOptionGroup,
    OptionGroup,
    Option,
    MenuItemStatus,
)
from ..schema import (
    MenuValidationRequest,
    MenuValidationResponse,
    ValidatedMenuItem,
    ValidatedOption,
)


def validate_menu(session: Session,restaurant_id: UUID,request: MenuValidationRequest,) -> MenuValidationResponse:

    validated_items = []

    for requested_item in request.items:

        menu_item = session.exec(
            select(MenuItem).where(
                MenuItem.id == requested_item.menu_item_id,
                MenuItem.restaurant_id == restaurant_id,
                MenuItem.status == MenuItemStatus.ACTIVE,
            )
        ).first()

        if not menu_item:
            raise ValueError(
                f"Menu item {requested_item.menu_item_id} "
                f"does not exist or is not available."
            )

        if requested_item.quantity <= 0:
            raise ValueError(
                f"Quantity for {menu_item.name} must be greater than 0."
            )


        option_groups = session.exec(
            select(OptionGroup)
            .join(
                MenuItemOptionGroup,
                MenuItemOptionGroup.option_group_id == OptionGroup.id,
            )
            .where(
                MenuItemOptionGroup.menu_item_id == menu_item.id,
                OptionGroup.restaurant_id == restaurant_id,
                OptionGroup.is_active == True,
            )
        ).all()



        group_ids = [group.id for group in option_groups]

        options = []

        if group_ids:
            options = session.exec(
                select(Option).where(
                    Option.option_group_id.in_(group_ids),
                    Option.is_active == True,
                )
            ).all()


        options_by_id = {
            option.id: option
            for option in options
        }


        selected_options = []

        for option_id in requested_item.option_ids:

            option = options_by_id.get(option_id)

            if not option:
                raise ValueError(
                    f"Option {option_id} is not valid for "
                    f"menu item {menu_item.name}."
                )

            selected_options.append(option)


        selected_by_group = {}

        for option in selected_options:
            selected_by_group.setdefault(
                option.option_group_id,
                []
            ).append(option)


        validated_options = []

        for group in option_groups:

            selected_in_group = selected_by_group.get(
                group.id,
                []
            )

            selection_count = len(selected_in_group)

            # Required group
            if group.is_required and selection_count == 0:
                raise ValueError(
                    f"{group.name} is required for "
                    f"{menu_item.name}."
                )

            # Minimum selections
            if selection_count < group.min_selections:
                raise ValueError(
                    f"{group.name} requires at least "
                    f"{group.min_selections} selection(s)."
                )

            # Maximum selections
            if selection_count > group.max_selections:
                raise ValueError(
                    f"{group.name} allows at most "
                    f"{group.max_selections} selection(s)."
                )


            for option in selected_in_group:

                validated_options.append(
                    ValidatedOption(
                        option_id=option.id,
                        name=option.name,
                        additional_price=option.additional_price,
                    )
                )



        validated_items.append(
            ValidatedMenuItem(
                menu_item_id=menu_item.id,
                name=menu_item.name,
                price=menu_item.price,
                quantity=requested_item.quantity,
                options=validated_options,
            )
        )



    return MenuValidationResponse(
        items=validated_items
    )