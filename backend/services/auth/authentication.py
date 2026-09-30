from sqlmodel import Session, select
from .models import Employee, EmployeeStatus
from .schemas import LoginRequest,TokenResponse
from .security.hashing import verify_password
from .security.jwt_utils import create_access_token, create_refresh_token

def login_employee(session: Session, login_data: LoginRequest) -> TokenResponse:
    
    employee = session.exec(select(Employee).where(Employee.email == login_data.email)).first()
    
    if not employee:
        raise ValueError("invalid email or password")

    if employee.status !=EmployeeStatus.ACTIVE:
        raise ValueError("this account is not active, see the admin")

    if not employee.password_hash:
        raise ValueError("The account hasn't been activated. contact the admin")

    if not verify_password(login_data.password, employee.password_hash):
        raise ValueError("invalid email or password")

    access_token = create_access_token(employee.id, employee.restaurant_id)
    refresh_token = create_refresh_token(employee.id, employee.restaurant_id)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)
