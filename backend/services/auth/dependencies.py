from .database import get_session
from fastapi import Depends, HTTPException,status
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from uuid import UUID
from sqlmodel import Session
from .security.jwt_utils import verify_token
from .models import Employee, EmployeeStatus

# this is to get the authorization bearer from the headers
security = HTTPBearer()

# this function is to get the current employee from the jwt from the request

def get_current_employee(session: Session=Depends(get_session),credentials:HTTPAuthorizationCredentials=Depends(security))->Employee:
    # this is the actual jwt
    token = credentials.credentials
    
    try:
        # we verify and decode the jwt
        payload = verify_token(token)
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