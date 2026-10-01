
from .database import SessionDep
from sqlmodel import select
from .models import (
    Employee,
    EmployeeStatus,
    EmployeeRole,
    RolePermission,
    Permission,
)

def get_user_permissions(session:SessionDep,employee_id):
    employee_permissions = session.exec(
        select(Permission.code)
        .join(RolePermission, Permission.id == RolePermission.permission_id)
        .join(EmployeeRole, EmployeeRole.role_id ==RolePermission.role_id)

        .where(EmployeeRole.employee_id ==employee_id)
        .distinct()
    ).all()
    return employee_permissions


def get_user_roles():
    pass
