from fastapi import Depends, HTTPException,status
from .utils import v_and_d
from fastapi.security import OAuth2PasswordBearer

oauthscheme = OAuth2PasswordBearer(tokenUrl="http://localhost:8000/auth/login")

def get_current_user(token:str = Depends(oauthscheme))->dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = v_and_d(token)

    employee_id = payload['sub']
    if employee_id is None or payload['type'] != "access":
        raise credentials_exception

    return payload

def require_permission(permission:str):
    def dependency(current_user=Depends(get_current_user)):
        if permission not in current_user.get("permissions"):
            raise HTTPException(
                status_code=403,
                detail="Permission denied"
            )
        return current_user
    
    return dependency
