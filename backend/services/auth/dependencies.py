from .database import get_session
from fastapi import Depends, HTTPException,status
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from uuid import UUID
from sqlmodel import Session, select
from .security.jwt_utils import verify_access_token
from .models import (
    Employee,
    EmployeeStatus,
    EmployeeRole,
    RolePermission,
    Permission,
)

# this is to get the authorization bearer from the headers
security = HTTPBearer()

# this function is to get the current employee from the jwt from the request

def get_current_employee(session: Session=Depends(get_session),credentials:HTTPAuthorizationCredentials=Depends(security))->Employee:
    # this is the actual jwt
    token = credentials.credentials
    
    try:
        # we verify and decode the jwt
        payload = verify_access_token(token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e),headers={"WWW-Authenticate": "Bearer"})
    employee_id = payload.get("sub")

    if not employee_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        employee_uuid = UUID(employee_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    employee = session.get(Employee, employee_uuid)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if employee.status != EmployeeStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Employee account is not active",
            headers={"WWW-Authenticate": "Bearer"},
        )

    

    return employee


def require_permission(permission_code:str):
    def permission_dependency(
            session:Session=Depends(get_session),
            current_employee:Employee=Depends(get_current_employee)
            )->Employee:
        permission = session.exec(
            select(Permission).where(Permission.code==permission_code)
        ).first()

        if not permission:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Permission is not configured",)

        has_permission = session.exec(
            select(EmployeeRole).join(
                RolePermission, EmployeeRole.role_id ==RolePermission.role_id
            ).where(current_employee.id ==EmployeeRole.employee_id, RolePermission.permission_id == permission.id)
        ).first()

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        return current_employee
    
    return permission_dependency

