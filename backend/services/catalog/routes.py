from fastapi import APIRouter, status, HTTPException,Depends
from .models import (Category,MenuItem,MenuItemOptionGroup,MenuItemStatus,Option,OptionGroup)
from .database import SessionDep
from .schema import CategoryResponse,CategoryCreate,CategoryUpdate
from .dependencies import require_permission
from .services.category_service import CategoryService
from uuid import UUID
# since the routes are not meaty i'll write them all in one file. if they later explode then i'll consider splitting them
router = APIRouter(tags=["Category"])
# Category routes
@router.post("/categories")
def create_category(session:SessionDep, category_data: CategoryCreate, current_user=Depends(require_permission("catalog:create"))):
    return CategoryService.create_category(session, current_user["restaurant_id"], category_data)

@router.post("/categories/{pk}")
def update_category(pk:UUID, session:SessionDep, category_data: CategoryUpdate, current_user=Depends(require_permission("catalog:update"))):
    return CategoryService.update_category(pk, category_data, session, current_user["restaurant_id"])

@router.get("/categories", response_model=list[CategoryResponse])
def get_categories(session: SessionDep, current_user= Depends(require_permission("catalog:view"))):
    return CategoryService.get_categories(session, current_user["restaurant_id"])


@router.get("/categories/{pk}", response_model=CategoryResponse)
def get_categories(pk:UUID, session: SessionDep, current_user= Depends(require_permission("catalog:view"))):
    return CategoryService.get_category(pk, session, current_user["restaurant_id"])


