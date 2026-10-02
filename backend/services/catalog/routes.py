from fastapi import APIRouter, status, HTTPException,Depends
from .models import (Category,MenuItem,MenuItemOptionGroup,MenuItemStatus,Option,OptionGroup)
from .database import SessionDep
from .schema import MenuResponse, CategoryResponse,CategoryCreate,CategoryUpdate, MenuItemResponse, MenuItemCreate,MenuItemUpdate,OptionGroupResponse,OptionGroupCreate,OptionGroupUpdate,OptionCreate,OptionResponse,OptionUpdate,MenuItemOptionGroupCreate,MenuItemOptionGroupResponse,MenuItemOptionGroupUpdate
from .dependencies import require_permission
from .services.category_service import CategoryService
from .services.menu_services import MenuService
from uuid import UUID
from .services.option_group_service import OptionGroupService
from .services.option_service import OptionService
from .services.menu_item_option_service import MenuItemOptionGroupService
from .services.pos_menu_service import MenuReadService


# since the routes are not meaty i'll write them all in one file. if they later explode then i'll consider splitting them
router = APIRouter(tags=["Menu Service"])
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

@router.get("/menus/{pk}", response_model=MenuItemResponse)
def get_menu_item(pk:UUID, session:SessionDep, current_user =Depends(require_permission("catalog:view"))):
    return MenuService.get_menu(pk,session,current_user["restaurant_id"])

@router.get("/menus", response_model=list[MenuItemResponse])
def get_menu_item(session:SessionDep, current_user =Depends(require_permission("catalog:view"))):
    return MenuService.get_menus(session,current_user["restaurant_id"])

@router.post("/menus", response_model=MenuItemResponse)
def create_menu_item(menu_data:MenuItemCreate, session:SessionDep, current_user=Depends(require_permission("catalog:create"))):
    return MenuService.create_menu(session, current_user["restaurant_id"],menu_data)

@router.patch("/menus/{pk}", response_model=MenuItemResponse)
def update_menu_item(pk,menu_data:MenuItemUpdate, session:SessionDep, current_user=Depends(require_permission("catalog:update"))):
    return MenuService.update_menu_item(pk,menu_data, session, current_user["restaurant_id"])


@router.delete("menus/{pk}")
def delete_menu(pk:UUID,session:SessionDep,current_user=Depends(require_permission("catalog:delete"))):
    return MenuService.delete_menu(pk, session, current_user["restaurant_id"])



@router.post(
    "/option-groups",
    response_model=OptionGroupResponse
)
def create_option_group(
    data: OptionGroupCreate,
    session: SessionDep,
    current_user=Depends(require_permission("catalog:create"))
):
    return OptionGroupService.create_option_group(
        session,
        current_user["restaurant_id"],
        data
    )


@router.get(
    "/option-groups",
    response_model=list[OptionGroupResponse]
)
def get_option_groups(
    session: SessionDep,
    current_user=Depends(require_permission("catalog:view"))
):
    return OptionGroupService.get_option_groups(
        session,
        current_user["restaurant_id"]
    )


@router.get(
    "/option-groups/{pk}",
    response_model=OptionGroupResponse
)
def get_option_group(
    pk: UUID,
    session: SessionDep,
    current_user=Depends(require_permission("catalog:view"))
):
    return OptionGroupService.get_option_group(
        pk,
        session,
        current_user["restaurant_id"]
    )


@router.patch(
    "/option-groups/{pk}",
    response_model=OptionGroupResponse
)
def update_option_group(
    pk: UUID,
    data: OptionGroupUpdate,
    session: SessionDep,
    current_user=Depends(require_permission("catalog:update"))
):
    return OptionGroupService.update_option_group(
        pk,
        data,
        session,
        current_user["restaurant_id"]
    )


@router.delete(
    "/option-groups/{pk}",
    status_code=204
)
def delete_option_group(
    pk: UUID,
    session: SessionDep,
    current_user=Depends(require_permission("catalog:delete"))
):
    OptionGroupService.delete_option_group(
        pk,
        session,
        current_user["restaurant_id"]
    )



@router.post(
    "/options",
    response_model=OptionResponse
)
def create_option(
    data: OptionCreate,
    session: SessionDep,
    current_user=Depends(require_permission("catalog:create"))
):
    return OptionService.create_option(
        session,
        current_user["restaurant_id"],
        data
    )


@router.get(
    "/options",
    response_model=list[OptionResponse]
)
def get_options(
    session: SessionDep,
    current_user=Depends(require_permission("catalog:view"))
):
    return OptionService.get_options(
        session,
        current_user["restaurant_id"]
    )


@router.get(
    "/options/{pk}",
    response_model=OptionResponse
)
def get_option(
    pk: UUID,
    session: SessionDep,
    current_user=Depends(require_permission("catalog:view"))
):
    return OptionService.get_option(
        pk,
        session,
        current_user["restaurant_id"]
    )


@router.patch(
    "/options/{pk}",
    response_model=OptionResponse
)
def update_option(
    pk: UUID,
    data: OptionUpdate,
    session: SessionDep,
    current_user=Depends(require_permission("catalog:update"))
):
    return OptionService.update_option(
        pk,
        data,
        session,
        current_user["restaurant_id"]
    )


@router.delete(
    "/options/{pk}",
    status_code=204
)
def delete_option(
    pk: UUID,
    session: SessionDep,
    current_user=Depends(require_permission("catalog:delete"))
):
    OptionService.delete_option(
        pk,
        session,
        current_user["restaurant_id"]
    )



@router.post(
    "/menu-option-groups",
    response_model=MenuItemOptionGroupResponse
)
def attach_option_group(
    data: MenuItemOptionGroupCreate,
    session: SessionDep,
    current_user=Depends(require_permission("catalog:update"))
):
    return MenuItemOptionGroupService.attach_option_group(
        session,
        current_user["restaurant_id"],
        data
    )


@router.get(
    "/menu-option-groups",
    response_model=list[MenuItemOptionGroupResponse]
)
def get_relationships(
    session: SessionDep,
    current_user=Depends(require_permission("catalog:view"))
):
    return MenuItemOptionGroupService.get_relationships(
        session,
        current_user["restaurant_id"]
    )


@router.get(
    "/menu-option-groups/{pk}",
    response_model=MenuItemOptionGroupResponse
)
def get_relationship(
    pk: UUID,
    session: SessionDep,
    current_user=Depends(require_permission("catalog:view"))
):
    return MenuItemOptionGroupService.get_relationship(
        pk,
        session,
        current_user["restaurant_id"]
    )


@router.patch(
    "/menu-option-groups/{pk}",
    response_model=MenuItemOptionGroupResponse
)
def update_relationship(
    pk: UUID,
    data: MenuItemOptionGroupUpdate,
    session: SessionDep,
    current_user=Depends(require_permission("catalog:update"))
):
    return MenuItemOptionGroupService.update_relationship(
        pk,
        data,
        session,
        current_user["restaurant_id"]
    )


@router.delete(
    "/menu-option-groups/{pk}",
    status_code=204
)
def detach_option_group(
    pk: UUID,
    session: SessionDep,
    current_user=Depends(require_permission("catalog:update"))
):
    MenuItemOptionGroupService.detach_option_group(
        pk,
        session,
        current_user["restaurant_id"]
    )



@router.get(
    "/menu",
    response_model=MenuResponse
)
def get_menu(
    session: SessionDep,
    current_user=Depends(require_permission("catalog:view"))
):
    return MenuReadService.get_menu(
        session,
        current_user["restaurant_id"]
    )