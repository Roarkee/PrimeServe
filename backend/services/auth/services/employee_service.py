from sqlmodel import Session, select
from ..models import Employee, EmployeeStatus,Role,EmployeeRole
from ..schemas import EmployeeCreate
from .invitation_service import create_employee_invitation



def create_employee_with_invitation(session: Session, employee_data: EmployeeCreate,
                                    current_employee:Employee)->tuple[Employee,str]:
    existing_employee = session.exec(
        select(Employee).where(Employee.email == employee_data.email)
    ).first()

    if existing_employee:
        raise ValueError("an employee with this email already exists")

    role = session.exec(
        select(Role).where(Role.id == employee_data.role_id)
    ).first()

    if not role:
        raise ValueError("invalid role assignment")

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

        employee_role = EmployeeRole(
            employee_id=employee.id,
            role_id=role.id,)

        session.add(employee_role)

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

