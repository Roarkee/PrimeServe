from ..schema import MenuItemCreate,MenuItemResponse,MenuItemUpdate
from ..models import MenuItem,Category
from sqlmodel import select,Session
from uuid import UUID
class MenuService:

    @staticmethod
    def create_menu(session:Session, restaurant_id, menu_data: MenuItemCreate):
        if menu_data.category_id is not None:
            category = session.exec(
                select(Category).where(
                    Category.id == menu_data.category_id,
                    Category.restaurant_id == restaurant_id
                )
            ).first()

            if category is None:
                raise ValueError("Category does not exist")

        menu = MenuItem(
            **menu_data.model_dump(),
            restaurant_id=restaurant_id
        )

        session.add(menu)
        session.commit()
        session.refresh(menu)

        return menu
        

    @staticmethod
    def update_menu_item(pk: UUID,data: MenuItemUpdate,session: Session,restaurant_id: UUID) -> MenuItem:

        menu_item = session.exec(
            select(MenuItem).where(
                MenuItem.id == pk,
                MenuItem.restaurant_id == restaurant_id
            )
        ).first()

        if menu_item is None:
            raise ValueError("No such menu item exists")

        updates = data.model_dump(exclude_unset=True)

        if "category_id" in updates and updates["category_id"] is not None:
            category = session.exec(
                select(Category).where(
                    Category.id == updates["category_id"],
                    Category.restaurant_id == restaurant_id
                )
            ).first()

            if category is None:
                raise ValueError("Category does not exist")

        for field, value in updates.items():
            setattr(menu_item, field, value)

        session.add(menu_item)
        session.commit()
        session.refresh(menu_item)

        return menu_item


    
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
    def get_menu(pk, session:Session, restaurant_id:UUID):
        menu_item = session.exec(
                            select(MenuItem).where(
                                MenuItem.id == pk,
                                MenuItem.restaurant_id == restaurant_id
                            )
                        ).first()
        if menu_item is None:
            raise ValueError("there's no menu like this")
        return menu_item
    
    @staticmethod
    def get_menus(session:Session, restaurant_id:UUID):
        menu_items = session.exec(
                            select(MenuItem).where( 
                                MenuItem.restaurant_id == restaurant_id
                            )
                        ).all()
        return menu_items