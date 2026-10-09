from fastapi import APIRouter, status, HTTPException,Depends
from .database import SessionDep
from .schemas.management_schema import (MenuResponse,
                    CategoryResponse,
                    CategoryCreate,
                    CategoryUpdate,
                    MenuItemResponse,
                    MenuItemCreate,
                    MenuItemUpdate,
                    OptionGroupResponse,
                    OptionGroupCreate,
                    OptionGroupUpdate,
                    OptionCreate,
                    OptionResponse,
                    OptionUpdate,
                    MenuItemOptionGroupCreate,
                    MenuItemOptionGroupResponse,MenuItemOptionGroupUpdate,
                    MenuValidationRequest,
                    MenuValidationResponse,
                    MenuItemMenuResponse)

from .schemas.pos_schema import MenuCreate
from .dependencies import require_permission
from .services.category_service import CategoryService
from .services.menu_services import MenuService
from uuid import UUID
from .services.option_group_service import OptionGroupService
from .services.option_service import OptionService
from .services.menu_item_option_service import MenuItemOptionGroupService
from .services.pos_menu_service import MenuReadService
from .services.validate_menu_service import validate_menu
from .utils import verify_internal_service

# since the routes are not meaty i'll write them all in one file. if they later explode then i'll consider splitting them
router = APIRouter(tags=["Menu Service"])
# Category routes
@router.post("/categories")
def create_category(session:SessionDep, category_data: CategoryCreate, current_user=Depends(require_permission("catalog:create"))):
    return CategoryService.create_category(session, current_user["restaurant_id"], category_data)

@router.patch("/categories/{pk}")
def update_category(pk:UUID, session:SessionDep, category_data: CategoryUpdate, current_user=Depends(require_permission("catalog:update"))):
    return CategoryService.update_category(pk, category_data, session, current_user["restaurant_id"])

@router.get("/categories", response_model=list[CategoryResponse])
def get_categories(session: SessionDep, current_user= Depends(require_permission("catalog:view"))):
    return CategoryService.get_categories(session, current_user["restaurant_id"])


@router.get("/category/{pk}", response_model=CategoryResponse)
def get_category(pk:UUID, session: SessionDep, current_user= Depends(require_permission("catalog:view"))):
    return CategoryService.get_category(pk, session, current_user["restaurant_id"])

@router.get("/menus/{pk}", response_model=MenuItemResponse)
def get_menu_item(pk:UUID, session:SessionDep, current_user =Depends(require_permission("catalog:view"))):
    return MenuService.get_menu(pk,session,current_user["restaurant_id"])

@router.get("/menus", response_model=list[MenuItemResponse])
def get_menu_items(session:SessionDep, current_user =Depends(require_permission("catalog:view"))):
    return MenuService.get_menus(session,current_user["restaurant_id"])

@router.post("/menus", response_model=MenuItemResponse)
def create_menu_item(menu_data:MenuItemCreate, session:SessionDep, current_user=Depends(require_permission("catalog:create"))):
    return MenuService.create_menu(session, current_user["restaurant_id"],menu_data)

@router.patch("/menus/{pk}", response_model=MenuItemResponse)
def update_menu_item(pk,menu_data:MenuItemUpdate, session:SessionDep, current_user=Depends(require_permission("catalog:update"))):
    return MenuService.update_menu_item(pk,menu_data, session, current_user["restaurant_id"])


@router.delete("/menus/{pk}")
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

    return MenuResponse(categories=[])
    return MenuReadService.get_menu(
        session,
        current_user["restaurant_id"]
    )

@router.post("/create_one_menu", response_model=MenuItemMenuResponse)
def create_menu(session:SessionDep,data:MenuCreate, current_user=Depends(require_permission("catalog:create"))):
    return MenuReadService.create_menu(session,data, current_user["restaurant_id"])




@router.post("/menu/validate", response_model=MenuValidationResponse)
def validate_menu_endpoint(request: MenuValidationRequest,session: SessionDep,
    _: bool = Depends(verify_internal_service),
):

    return validate_menu(
        session=session,
        restaurant_id=request.restaurant_id,
        request=request,
    )





from sqlalchemy import text
import time

# @router.get("/db-test")
# def db_test(session: SessionDep):
#     times = []

#     for _ in range(5):
#         start = time.perf_counter()

#         session.exec(text("SELECT 1")).first()

#         times.append(time.perf_counter() - start)

#     return {"times": times}

@router.get("/db-test")
def db_test():
    from sqlalchemy import text
    from sqlmodel import Session
    from .database import engine
    import time

    times = []

    for _ in range(5):
        start = time.perf_counter()

        with Session(engine) as session:
            session.exec(text("SELECT 1")).first()

        times.append(time.perf_counter() - start)

    return {"times": times}

# Adjust to your actual import


@router.get("/db-diagnostic")
def db_diagnostic():



    from sqlalchemy import text
    from sqlmodel import Session
    import time
    from .database import engine

    def measure_query_latency(engine):
       
        results = []

        with Session(engine) as session:
            session.connection()

            for _ in range(10):
                start = time.perf_counter()

                row = session.exec(text("""
                    SELECT
                        EXTRACT(
                            EPOCH FROM
                            (clock_timestamp() - statement_timestamp())
                        ) * 1000 AS server_elapsed_ms,
                        pg_sleep(0.01)
                """)).first()

                client_elapsed_ms = (
                    time.perf_counter() - start
                ) * 1000

                results.append({
                    "server_elapsed_ms": round(
                        float(row[0] or 0), 3
                    ),
                    "client_elapsed_ms": round(
                        client_elapsed_ms, 2
                    ),
                })

        return results
    return measure_query_latency(engine)

    
    import time
    from sqlalchemy import text
    from sqlmodel import Session

    from .database import engine  
    with Session(engine) as session:
        start = time.perf_counter()
        session.connection()
        checkout_ms = (time.perf_counter() - start) * 1000

        query_times = []

        for _ in range(5):
            start = time.perf_counter()
            session.exec(text("SELECT 1")).first()
            query_times.append(round((time.perf_counter() - start) * 1000, 2))

    return {
        "connection_checkout_ms": round(checkout_ms, 2),
        "select_1_times_ms": query_times,
    }






@router.get("/db-roundtrip-diagnostic")
def db_diagnostic_roundtrip(
    current_user=Depends(require_permission("catalog:view")),
):
    from sqlmodel import Session
    from .database import engine

    results = []

    with Session(engine) as session:
        # Measure obtaining a database connection.
        start = time.perf_counter()
        session.connection()
        checkout_ms = (time.perf_counter() - start) * 1000

        # Separate the first query from repeated queries.
        start = time.perf_counter()
        session.exec(text("SELECT 1")).first()
        warmup_ms = (time.perf_counter() - start) * 1000

        # Reuse the same checked-out connection.
        for i in range(10):
            start = time.perf_counter()
            session.exec(text("SELECT 1")).first()
            elapsed_ms = (time.perf_counter() - start) * 1000

            results.append({
                "query": i + 1,
                "client_elapsed_ms": round(elapsed_ms, 2),
            })

    return {
        "connection_checkout_ms": round(checkout_ms, 2),
        "warmup_query_ms": round(warmup_ms, 2),
        "repeated_queries": results,
    }


