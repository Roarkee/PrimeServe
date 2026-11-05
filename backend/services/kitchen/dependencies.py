from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status
from .utils import verify_decode_token

bearer = HTTPBearer()


def get_user(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    token = credentials.credentials
    return verify_decode_token(token)


def require_permission(permission: str):
    def dependency(current_user: dict = Depends(get_user)) -> dict:
        permissions = current_user.get("permissions", [])
        if permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: required '{permission}'",
            )
        return current_user

    return dependency
