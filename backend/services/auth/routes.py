from fastapi import Depends, HTTPException, APIRouter,status
from sqlmodel import Session,select
from uuid import UUID
from .models import Role
from .database import get_session
from .schemas import (
    LoginRequest,
    TokenResponse,
    InvitationAccept,
    EmployeeResponse,
    EmployeeCreate,
    EmployeeInvitationResponse,
    RefreshTokenRequest
)
from .auth import login_employee
from .services.invitation_service import accept_invitation
from .services.employee_service import create_employee_with_invitation
from .dependencies import require_permission, get_current_employee
from .models import Employee
from .security.jwt_utils import verify_access_token,verify_refresh_token,create_access_token


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

@router.post("/employees",response_model=EmployeeInvitationResponse)
def register_employees(employee_data:EmployeeCreate, current_employee:Employee = Depends(require_permission("employee:create")), session:Session = Depends(get_session)):
    try:
        employee, token = create_employee_with_invitation(
            session=session,
            employee_data=employee_data,
            current_employee=current_employee,
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

@router.post("/refresh", response_model=TokenResponse)
def refresh(refresh_data:RefreshTokenRequest):
    try:
        payload = verify_refresh_token(refresh_data.refresh_token)
        # employee id is signed as a str so you always have to convert it back to python uuid
        employee_id = UUID(payload["sub"])
        restaurant_id = UUID(payload["restaurant_id"])

        access_token = create_access_token(
            employee_id=employee_id,
            restaurant_id=restaurant_id,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_data.refresh_token,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/roles", response_model=list[Role])
def roles(session: Session=Depends(get_session), current_user: Employee=Depends(require_permission)):
    return session.exec(
        select(Role).order_by(Role.name)
    ).all()

   