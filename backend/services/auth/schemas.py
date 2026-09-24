
from uuid import UUID

from pydantic import BaseModel, EmailStr,ConfigDict

from .models import EmployeeStatus


class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class InvitationAccept(BaseModel):
    token: str
    password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class EmployeeResponse(BaseModel):
    id: UUID
    restaurant_id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None
    status: EmployeeStatus

    model_config = ConfigDict(from_attributes=True)

class EmployeeInvitationResponse(BaseModel):
    employee: EmployeeResponse
    invitation_token: str