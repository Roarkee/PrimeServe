from sqlmodel import Session, select
from ..models import Employee, EmployeeStatus
from ..schemas import EmployeeCreate
from .invitation_service import create_employee_invitation



def create_employee_with_invitation(session: Session, employee_data: EmployeeCreate,
                                    current_employee:Employee)->tuple[Employee,str]:
    existing_employee = session.exec(
        select(Employee).where(Employee.email == employee_data.email)
    ).first()

    if existing_employee:
        raise ValueError("an employee with this email already exists")
    

    employee = Employee(
        restaurant_id=current_employee.restaurant_id,
        first_name=employee_data.first_name,
        last_name=employee_data.last_name,
        email=employee_data.email,
        phone=employee_data.phone,
        password_hash=None,
        status=EmployeeStatus.INACTIVE,
    )
    try:
        session.add(employee)
        session.flush()

        token = create_employee_invitation(
            session=session,
            employee=employee,
            current_employee=current_employee,
        )

        session.commit()
        session.refresh(employee)

        return employee, token

    except Exception:
        session.rollback()
        raise

