import uuid
from enum import Enum
from sqlmodel import Field, SQLModel,DateTime
from datetime import datetime, timezone

AUTH_SCHEMA = "prime_auth"

class EmployeeStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class Employee(SQLModel, table=True):
    __tablename__ = "employees"
    __table_args__ = {"schema": AUTH_SCHEMA}

    id: uuid.UUID = Field(default_factory=uuid.uuid4,primary_key=True,)
    restaurant_id: uuid.UUID = Field(nullable=False,)
    first_name: str = Field(max_length=50,nullable=False,)
    last_name: str = Field(max_length=50,nullable=False,)
    email: str = Field(max_length=100,nullable=False, unique=True)
    phone: str | None = Field(default=None,max_length=20)
    password_hash: str |None= Field(max_length=255,default=None,)
    status: EmployeeStatus = Field(default=EmployeeStatus.ACTIVE, nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),nullable=False,sa_type=DateTime(timezone=True),)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),nullable=False,sa_type=DateTime(timezone=True),)


class Role(SQLModel, table=True):
    __tablename__ = "roles"
    __table_args__ = {"schema": AUTH_SCHEMA}

    id: uuid.UUID = Field(default_factory=uuid.uuid4,primary_key=True,)
    name: str = Field(max_length=50,nullable=False,)


class Permission(SQLModel, table=True):
    __tablename__ = "permissions"
    __table_args__ = {"schema": AUTH_SCHEMA}

    id: uuid.UUID = Field(default_factory=uuid.uuid4,primary_key=True,)
    code: str = Field(max_length=50,nullable=False,unique=True,)
    description: str | None = Field(default=None,)


class EmployeeRole(SQLModel, table=True):
    __tablename__ = "employee_roles"
    __table_args__ = {"schema": AUTH_SCHEMA}

    employee_id: uuid.UUID = Field(primary_key=True,foreign_key="prime_auth.employees.id",)
    role_id: uuid.UUID = Field(primary_key=True,foreign_key="prime_auth.roles.id",)


class RolePermission(SQLModel, table=True):
    __tablename__ = "role_permissions"
    __table_args__ = {"schema": AUTH_SCHEMA}

    role_id: uuid.UUID = Field(primary_key=True,foreign_key="prime_auth.roles.id",)
    permission_id: uuid.UUID = Field(primary_key=True,foreign_key="prime_auth.permissions.id",)


class EmployeeBranch(SQLModel, table=True):
    __tablename__ = "employee_branches"
    __table_args__ = {"schema": AUTH_SCHEMA}

    employee_id: uuid.UUID = Field(primary_key=True,foreign_key="prime_auth.employees.id",)
    branch_id: uuid.UUID = Field(primary_key=True,)


class EmployeeInvitation(SQLModel, table=True):
    __tablename__ = "employee_invitations"
    __table_args__ = {"schema": AUTH_SCHEMA}

    id: uuid.UUID = Field(default_factory=uuid.uuid4,primary_key=True,)
    employee_id: uuid.UUID = Field(foreign_key="prime_auth.employees.id",nullable=False,)
    email: str = Field(max_length=100,nullable=False,)
    token_hash: str = Field(max_length=255,nullable=False,unique=True,)
    expires_at: datetime = Field(nullable=False,sa_type=DateTime(timezone=True),)
    accepted_at: datetime | None = Field(default=None,sa_type=DateTime(timezone=True),)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),nullable=False,sa_type=DateTime(timezone=True),)
    created_by: uuid.UUID = Field( foreign_key="prime_auth.employees.id",nullable=False,)

class PasswordReset(SQLModel, table=True):
    __tablename__ = "password_resets"
    __table_args__ = {"schema": AUTH_SCHEMA}

    id: uuid.UUID = Field(default_factory=uuid.uuid4,primary_key=True,)
    employee_id: uuid.UUID = Field(foreign_key="prime_auth.employees.id",nullable=False,)
    token_hash: str = Field(max_length=255,nullable=False,unique=True,)
    expires_at: datetime = Field(nullable=False,sa_type=DateTime(timezone=True),)
    used_at: datetime | None = Field(default=None,sa_type=DateTime(timezone=True),)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),nullable=False,sa_type=DateTime(timezone=True),)