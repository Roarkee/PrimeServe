from sqlmodel import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends,HTTPException,status
from .utils import verify_decode_token
bearer = HTTPBearer()


def get_user(credentials: HTTPAuthorizationCredentials=Depends(bearer))->dict:
    token = credentials.credentials
    credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = verify_decode_token(token)
    if payload['sub'] is None or payload['type'] != 'access':
        raise credentials_exception

    return payload

def require_permission(permission:str):
    def dependency(current_user=Depends(get_user)):
            if permission not in current_user.get("permissions",[]):
                raise HTTPException(
                    status_code=403,
                    detail="Permission denied"
                )
            return current_user
        
    return dependency
    