from uuid import UUID
import secrets
import hashlib
from sqlmodel import Session, select
from datetime import timedelta,datetime,timezone
from ..models import EmployeeInvitation, Employee, EmployeeStatus
from ..security.hashing import hash_password

INVITATION_EXPIRES_HOURS = 48

def generate_token()->str:
   token = secrets.token_urlsafe(32)
   return token

def hash_token(token: str) ->str:
   return hashlib.sha256(token.encode('utf-8')).hexdigest()



def create_employee_invitation(employee: Employee, session: Session, created_by:UUID)->str:

   
    employee_invitations = session.exec(select(EmployeeInvitation).where(
      EmployeeInvitation.employee_id==employee.id, 
      EmployeeInvitation.accepted_at.is_(None))).all()
#    we're invalidating all invitations

    now = datetime.now(timezone.utc)
    for invitations in employee_invitations:
       invitations.expires_at = now

    token = generate_token()
    # so here we store the token hash in the db not the raw one
    invitation = EmployeeInvitation(
        employee_id=employee.id,
        email=employee.email,
        token_hash=hash_token(token),
        expires_at=now + timedelta(
            hours=INVITATION_EXPIRES_HOURS
        ),
        created_by=created_by,
    )
    session.add(invitation)
    return token

def accept_invitation(session:Session, token:str, password:str)->Employee:
    hashed_token = hash_token(token)

    invitation = session.exec(
       select(EmployeeInvitation)
       .where(EmployeeInvitation.token_hash==hashed_token)).first()
    if not invitation:
       raise ValueError("user has not been invited into this restaurant")
    if invitation.accepted_at is not None:
       raise ValueError("invitation has already been used")
    now = datetime.now(timezone.utc)
    if invitation.expires_at <= now:
        raise ValueError("invitation has expired")

    employee = session.get(Employee, invitation.employee_id)
    if not employee:
       raise ValueError("employee no doesn't exist")
    employee.password_hash = hash_password(password)
    employee.status = EmployeeStatus.ACTIVE
    employee.updated_at = now

    invitation.accepted_at = now
    session.add(employee)
    session.add(invitation)

    session.commit()
    session.refresh(employee)
    return employee