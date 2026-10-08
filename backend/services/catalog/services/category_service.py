from sqlmodel import select, Session
from ..models import Category
from ..schemas.management_schema import CategoryCreate,CategoryUpdate,CategoryReorder,CategoryResponse
from uuid import UUID

class CategoryService:
    @staticmethod
    def create_category(session: Session, restaurant_id, category_data:CategoryCreate)->Category:

        category = Category(**category_data.model_dump(), restaurant_id=restaurant_id)
        session.add(category)
        session.commit()
        session.refresh(category)
        return category

    @staticmethod
    def get_category(pk:UUID, session:Session, restaurant_id)->Category:
        category = session.exec(
            select(Category).where(Category.id == pk, Category.restaurant_id==restaurant_id)
        ).first()
        if category is None:
            raise ValueError("no such category exists")
        return category

    @staticmethod
    def get_categories(session:Session, restaurant_id)->list[Category]:
        categories = session.exec(
                    select(Category).where(Category.restaurant_id==restaurant_id)
                ).all()
        if categories is None:
            raise ValueError("add a new category to get started")
        return categories

    @staticmethod
    def update_category(pk:UUID, data:CategoryUpdate, session:Session, restaurant_id):
        category = session.exec(
            select(Category).where(
                Category.id == pk,
                Category.restaurant_id == restaurant_id)
        ).first()

        if category is None:
            raise ValueError("no category exists")
    # so that it doesn't accidentally set the optional values to None
        updates = data.model_dump(exclude_unset=True)

        for field, value in updates.items():
            setattr(category, field, value)

        session.add(category)
        session.commit()
        session.refresh(category)
        return category


    

    def delete_category(pk:UUID, session: Session, restaurant_id):
        category = session.exec(
            select(Category).where(
                Category.id == pk,
                Category.restaurant_id == restaurant_id,
            )
        ).first()

        if category is None:
            raise ValueError("No such category exists")

        session.delete(category)
        session.commit()