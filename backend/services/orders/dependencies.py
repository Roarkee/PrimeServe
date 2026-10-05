from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from dotenv import load_dotenv
import os
load_dotenv()


bearer_scheme = HTTPBearer()

def get_current_employee(
     credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            os.getenv("SECRET_KEY"),
            algorithms=[os.getenv("JWT_ALGO")],
        )

        employee_id = payload.get("sub")
        restaurant_id = payload.get("restaurant_id")
        permissions = payload.get("permissions", [])

        if not employee_id or not restaurant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials.",
            )

        return {
            "employee_id": UUID(employee_id),
            "restaurant_id": UUID(restaurant_id),
            "permissions": permissions,
        }

    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
        )


def require_permission(permission: str):

    def dependency(
        current_employee=Depends(get_current_employee),
    ):
        if permission not in current_employee["permissions"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )

        return current_employee

    return dependency

