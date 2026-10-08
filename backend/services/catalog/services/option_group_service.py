from uuid import UUID

from sqlmodel import Session, select

from ..models import OptionGroup
from ..schemas.management_schema import OptionGroupCreate, OptionGroupUpdate


class OptionGroupService:

    @staticmethod
    def create_option_group(
        session: Session,
        restaurant_id: UUID,
        data: OptionGroupCreate
    ) -> OptionGroup:

        if data.min_selections < 0:
            raise ValueError("min_selections cannot be negative")

        if data.max_selections < 0:
            raise ValueError("max_selections cannot be negative")

        if data.min_selections > data.max_selections:
            raise ValueError("min_selections cannot exceed max_selections")

        if data.is_required and data.min_selections < 1:
            raise ValueError(
                "A required option group must have at least one minimum selection"
            )

        option_group = OptionGroup(
            **data.model_dump(),
            restaurant_id=restaurant_id
        )

        session.add(option_group)
        session.commit()
        session.refresh(option_group)

        return option_group

    @staticmethod
    def get_option_group(
        pk: UUID,
        session: Session,
        restaurant_id: UUID
    ) -> OptionGroup:

        option_group = session.exec(
            select(OptionGroup).where(
                OptionGroup.id == pk,
                OptionGroup.restaurant_id == restaurant_id
            )
        ).first()

        if option_group is None:
            raise ValueError("No such option group exists")

        return option_group

    @staticmethod
    def get_option_groups(
        session: Session,
        restaurant_id: UUID
    ) -> list[OptionGroup]:

        return session.exec(
            select(OptionGroup).where(
                OptionGroup.restaurant_id == restaurant_id
            )
        ).all()

    @staticmethod
    def update_option_group(
        pk: UUID,
        data: OptionGroupUpdate,
        session: Session,
        restaurant_id: UUID
    ) -> OptionGroup:

        option_group = session.exec(
            select(OptionGroup).where(
                OptionGroup.id == pk,
                OptionGroup.restaurant_id == restaurant_id
            )
        ).first()

        if option_group is None:
            raise ValueError("No such option group exists")

        updates = data.model_dump(exclude_unset=True)

        min_selections = updates.get(
            "min_selections",
            option_group.min_selections
        )

        max_selections = updates.get(
            "max_selections",
            option_group.max_selections
        )

        is_required = updates.get(
            "is_required",
            option_group.is_required
        )

        if min_selections < 0:
            raise ValueError("min_selections cannot be negative")

        if max_selections < 0:
            raise ValueError("max_selections cannot be negative")

        if min_selections > max_selections:
            raise ValueError("min_selections cannot exceed max_selections")

        if is_required and min_selections < 1:
            raise ValueError(
                "A required option group must have at least one minimum selection"
            )

        for field, value in updates.items():
            setattr(option_group, field, value)

        session.add(option_group)
        session.commit()
        session.refresh(option_group)

        return option_group

    @staticmethod
    def delete_option_group(
        pk: UUID,
        session: Session,
        restaurant_id: UUID
    ) -> None:

        option_group = session.exec(
            select(OptionGroup).where(
                OptionGroup.id == pk,
                OptionGroup.restaurant_id == restaurant_id
            )
        ).first()

        if option_group is None:
            raise ValueError("No such option group exists")

        session.delete(option_group)
        session.commit()