from fastapi import Depends, HTTPException, APIRouter
from sqlmodel import Session

from .database import get_session
from .schemas import (
    LoginRequest,
    TokenResponse,
    InvitationAccept,
    EmployeeResponse,
    EmployeeCreate,
    EmployeeInvitationResponse
)
from .auth import login_employee
from .services.invitation_service import accept_invitation
from .services.employee_service import create_employee_with_invitation



router = APIRouter(prefix="/auth", tags=["Authentication"])
@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, session:Session=Depends(get_session)):
    try:
        return login_employee(session, login_data)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/invitation/accept", response_model=EmployeeResponse)
def accept_invitation_route(invitation_data: InvitationAccept, session:Session = Depends(get_session)):
    try:
        return accept_invitation(
            session=session,
            token=invitation_data.token,
            password=invitation_data.password,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
from uuid import UUID
@router.post("/employees",response_model=EmployeeInvitationResponse)
def register_employees(employee_data:EmployeeCreate, restaurant_id:UUID, created_by:UUID, session:Session = Depends(get_session)):
    try:
        employee, token = create_employee_with_invitation(
            session=session,
            employee_data=employee_data,
            restaurant_id=restaurant_id,
            created_by=created_by,
        )

        return EmployeeInvitationResponse(
            employee=employee,
            invitation_token=token,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )