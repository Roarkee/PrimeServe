
from ..models import MenuItemRouting, PrepStation
from ..schema.schema import MenuRoute
from sqlmodel import Session, select
from ..exceptions import AlreadyExistsError

def create_menu_route(session: Session, restaurant_id, station_id, menu_item_id) -> MenuRoute:
    exists = session.exec(
        select(1)
        .select_from(MenuItemRouting)
        .where(MenuItemRouting.restaurant_id == restaurant_id,
               MenuItemRouting.station_id ==station_id,
               MenuItemRouting.menu_item_id == menu_item_id)
        .exists()
    )

    if exists:
        raise AlreadyExistsError("this route has been defined already, move on sherlock")

    menu_route = MenuItemRouting(restaurant_id=restaurant_id,
                                 station_id=station_id,
                                 )
    session.add(menu_route)
    session.commit()
    return MenuRoute(menu_route.id,
                     menu_route.restaurant_id,
                     menu_route.station_id,
                     menu_route.is_active)
    
    