from decimal import Decimal
from uuid import UUID

from sqlmodel import Session, select

from ..models import Option, OptionGroup
from ..schemas.management_schema import OptionCreate, OptionUpdate


class OptionService:

    @staticmethod
    def create_option(
        session: Session,
        restaurant_id: UUID,
        data: OptionCreate
    ) -> Option:

        option_group = session.exec(
            select(OptionGroup).where(
                OptionGroup.id == data.option_group_id,
                OptionGroup.restaurant_id == restaurant_id
            )
        ).first()

        if option_group is None:
            raise ValueError("Option group does not exist")

        if data.additional_price < Decimal("0.00"):
            raise ValueError("additional_price cannot be negative")

        option = Option(
            **data.model_dump(),
        )

        session.add(option)
        session.commit()
        session.refresh(option)

        return option

    @staticmethod
    def get_option(
        pk: UUID,
        session: Session,
        restaurant_id: UUID
    ) -> Option:

        option = session.exec(
            select(Option)
            .join(
                OptionGroup,
                Option.option_group_id == OptionGroup.id
            )
            .where(
                Option.id == pk,
                OptionGroup.restaurant_id == restaurant_id
            )
        ).first()

        if option is None:
            raise ValueError("No such option exists")

        return option

    @staticmethod
    def get_options(
        session: Session,
        restaurant_id: UUID
    ) -> list[Option]:

        return session.exec(
            select(Option)
            .join(
                OptionGroup,
                Option.option_group_id == OptionGroup.id
            )
            .where(
                OptionGroup.restaurant_id == restaurant_id
            )
        ).all()

    @staticmethod
    def update_option(
        pk: UUID,
        data: OptionUpdate,
        session: Session,
        restaurant_id: UUID
    ) -> Option:

        option = session.exec(
            select(Option)
            .join(
                OptionGroup,
                Option.option_group_id == OptionGroup.id
            )
            .where(
                Option.id == pk,
                OptionGroup.restaurant_id == restaurant_id
            )
        ).first()

        if option is None:
            raise ValueError("No such option exists")

        updates = data.model_dump(exclude_unset=True)

        if "option_group_id" in updates:
            new_group = session.exec(
                select(OptionGroup).where(
                    OptionGroup.id == updates["option_group_id"],
                    OptionGroup.restaurant_id == restaurant_id
                )
            ).first()

            if new_group is None:
                raise ValueError("Option group does not exist")

        if "additional_price" in updates:
            if updates["additional_price"] < Decimal("0.00"):
                raise ValueError("additional_price cannot be negative")

        for field, value in updates.items():
            setattr(option, field, value)

        session.add(option)
        session.commit()
        session.refresh(option)

        return option

    @staticmethod
    def delete_option(
        pk: UUID,
        session: Session,
        restaurant_id: UUID
    ) -> None:

        option = session.exec(
            select(Option)
            .join(
                OptionGroup,
                Option.option_group_id == OptionGroup.id
            )
            .where(
                Option.id == pk,
                OptionGroup.restaurant_id == restaurant_id
            )
        ).first()

        if option is None:
            raise ValueError("No such option exists")

        session.delete(option)
        session.commit()