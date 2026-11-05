from uuid import UUID
from sqlmodel import Session, select

from ..models import MenuItemRouting, PrepStation
from ..exceptions import AlreadyExistsError, NotFoundError


def create_menu_route(
    session: Session,
    restaurant_id: UUID,
    station_id: UUID,
    menu_item_id: UUID,
) -> MenuItemRouting:
    """
    Create a new routing assignment between a menu item and a prep station.
    Validates station existence, activity, and restaurant tenant isolation.
    """
    # Verify prep station exists, belongs to the restaurant, and is active
    station = session.exec(
        select(PrepStation).where(
            PrepStation.id == station_id,
            PrepStation.restaurant_id == restaurant_id,
            PrepStation.is_active.is_(True),
        )
    ).first()

    if station is None:
        raise NotFoundError("Prep station not found, inactive, or belongs to another restaurant")

    # Check for existing route
    existing_route = session.exec(
        select(MenuItemRouting).where(
            MenuItemRouting.restaurant_id == restaurant_id,
            MenuItemRouting.station_id == station_id,
            MenuItemRouting.menu_item_id == menu_item_id,
        )
    ).first()

    if existing_route:
        if existing_route.is_active:
            raise AlreadyExistsError("Routing for this menu item and prep station already exists")
        # If previously deactivated, reactivate it
        existing_route.is_active = True
        session.add(existing_route)
        session.commit()
        session.refresh(existing_route)
        return existing_route

    route = MenuItemRouting(
        restaurant_id=restaurant_id,
        station_id=station_id,
        menu_item_id=menu_item_id,
        is_active=True,
    )
    session.add(route)
    session.commit()
    session.refresh(route)
    return route
