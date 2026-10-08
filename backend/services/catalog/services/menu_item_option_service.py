from uuid import UUID

from sqlmodel import Session, select

from ..models import MenuItem, OptionGroup, MenuItemOptionGroup
from ..schemas.management_schema import (
    MenuItemOptionGroupCreate,
    MenuItemOptionGroupUpdate,
)


class MenuItemOptionGroupService:

    @staticmethod
    def attach_option_group(
        session: Session,
        restaurant_id: UUID,
        data: MenuItemOptionGroupCreate
    ) -> MenuItemOptionGroup:

        menu_item = session.exec(
            select(MenuItem).where(
                MenuItem.id == data.menu_item_id,
                MenuItem.restaurant_id == restaurant_id
            )
        ).first()

        if menu_item is None:
            raise ValueError("Menu item does not exist")

        option_group = session.exec(
            select(OptionGroup).where(
                OptionGroup.id == data.option_group_id,
                OptionGroup.restaurant_id == restaurant_id
            )
        ).first()

        if option_group is None:
            raise ValueError("Option group does not exist")

        existing = session.exec(
            select(MenuItemOptionGroup).where(
                MenuItemOptionGroup.menu_item_id == data.menu_item_id,
                MenuItemOptionGroup.option_group_id == data.option_group_id
            )
        ).first()

        if existing is not None:
            raise ValueError(
                "Option group is already attached to this menu item"
            )

        relationship = MenuItemOptionGroup(
            **data.model_dump()
        )

        session.add(relationship)
        session.commit()
        session.refresh(relationship)

        return relationship

    @staticmethod
    def get_relationship(
        pk: UUID,
        session: Session,
        restaurant_id: UUID
    ) -> MenuItemOptionGroup:

        relationship = session.exec(
            select(MenuItemOptionGroup)
            .join(
                MenuItem,
                MenuItemOptionGroup.menu_item_id == MenuItem.id
            )
            .where(
                MenuItemOptionGroup.id == pk,
                MenuItem.restaurant_id == restaurant_id
            )
        ).first()

        if relationship is None:
            raise ValueError("No such relationship exists")

        return relationship

    @staticmethod
    def get_relationships(
        session: Session,
        restaurant_id: UUID
    ) -> list[MenuItemOptionGroup]:

        return session.exec(
            select(MenuItemOptionGroup)
            .join(
                MenuItem,
                MenuItemOptionGroup.menu_item_id == MenuItem.id
            )
            .where(
                MenuItem.restaurant_id == restaurant_id
            )
        ).all()

    @staticmethod
    def update_relationship(
        pk: UUID,
        data: MenuItemOptionGroupUpdate,
        session: Session,
        restaurant_id: UUID
    ) -> MenuItemOptionGroup:

        relationship = session.exec(
            select(MenuItemOptionGroup)
            .join(
                MenuItem,
                MenuItemOptionGroup.menu_item_id == MenuItem.id
            )
            .where(
                MenuItemOptionGroup.id == pk,
                MenuItem.restaurant_id == restaurant_id
            )
        ).first()

        if relationship is None:
            raise ValueError("No such relationship exists")

        updates = data.model_dump(exclude_unset=True)

        for field, value in updates.items():
            setattr(relationship, field, value)

        session.add(relationship)
        session.commit()
        session.refresh(relationship)

        return relationship

    @staticmethod
    def detach_option_group(
        pk: UUID,
        session: Session,
        restaurant_id: UUID
    ) -> None:

        relationship = session.exec(
            select(MenuItemOptionGroup)
            .join(
                MenuItem,
                MenuItemOptionGroup.menu_item_id == MenuItem.id
            )
            .where(
                MenuItemOptionGroup.id == pk,
                MenuItem.restaurant_id == restaurant_id
            )
        ).first()

        if relationship is None:
            raise ValueError("No such relationship exists")

        session.delete(relationship)
        session.commit()