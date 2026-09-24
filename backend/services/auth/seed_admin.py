
import os
import uuid

from dotenv import load_dotenv
from sqlmodel import Session, select

from .database import engine
from .models import (
    Employee,
    EmployeeRole,
    EmployeeStatus,
    Role,
)
from .security.hashing import hash_password


load_dotenv()

RESTAURANT_ID = uuid.UUID(
    os.getenv(
        "SEED_RESTAURANT_ID",
        "550e8400-e29b-41d4-a716-446655440000",
    )
)

ADMIN_EMAIL = os.getenv(
    "SEED_ADMIN_EMAIL",
    "rikkardambrose0@gmail.com",
)

ADMIN_PASSWORD = os.getenv(
    "SEED_ADMIN_PASSWORD",
    "henorkam",
)

FIRST_NAME = "PrimeServe"
LAST_NAME = "Admin"


def seed_admin():
    with Session(engine) as session:

        # Check whether the admin already exists
        existing_employee = session.exec(
            select(Employee).where(
                Employee.email == ADMIN_EMAIL
            )
        ).first()

        if existing_employee:
            print(f"Admin already exists: {existing_employee.email}")
            print(f"Admin ID: {existing_employee.id}")
            print(f"Restaurant ID: {existing_employee.restaurant_id}")
            return

        # Create admin employee
        admin = Employee(
            restaurant_id=RESTAURANT_ID,
            first_name=FIRST_NAME,
            last_name=LAST_NAME,
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
            status=EmployeeStatus.ACTIVE,
        )

        session.add(admin)
        session.flush()

        # Create ADMIN role for this restaurant
        admin_role = session.exec(
            select(Role).where(
                Role.restaurant_id == RESTAURANT_ID,
                Role.name == "ADMIN",
            )
        ).first()

        if not admin_role:
            admin_role = Role(
                restaurant_id=RESTAURANT_ID,
                name="ADMIN",
            )
            session.add(admin_role)
            session.flush()

        # Assign ADMIN role to employee
        employee_role = EmployeeRole(
            employee_id=admin.id,
            role_id=admin_role.id,
        )

        session.add(employee_role)

        session.commit()

        print("\nAdmin created successfully!")
        print("--------------------------------")
        print(f"Admin ID:       {admin.id}")
        print(f"Restaurant ID:  {RESTAURANT_ID}")
        print(f"Email:          {ADMIN_EMAIL}")
        print(f"Password:       {ADMIN_PASSWORD}")
        print(f"Role:           ADMIN")
        print("--------------------------------")


if __name__ == "__main__":
    seed_admin()
