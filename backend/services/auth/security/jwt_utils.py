import os
import jwt
from datetime import datetime, timedelta, timezone
from uuid import UUID
from dotenv import load_dotenv
from fastapi.exceptions import HTTPException
load_dotenv()

JWT_SECRET_KEY = os.getenv("SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY not set")

JWT_ALGO = "HS256"

ACCESS_TOKEN_EXPIRES_MINUTES = 30
REFRESH_TOKEN_EXPIRES_DAYS = 7


def create_access_token(employee_id:UUID, restaurant_id: UUID)->str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(employee_id),
        "restaurant_id": str(restaurant_id),
        "type": "access",
        "iat": now,
        "exp": now +timedelta(minutes = ACCESS_TOKEN_EXPIRES_MINUTES)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGO)

def create_refresh_token(employee_id: UUID, restaurant_id: UUID) ->str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(employee_id),
        "restaurant_id": str(restaurant_id),
        "type": "refresh",
        "iat": now,
        "exp": now +timedelta(days=REFRESH_TOKEN_EXPIRES_DAYS)

    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGO)



def decode_token(token:str)->dict:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=JWT_ALGO)
        return payload
    except jwt.ExpiredSignatureError:
            raise ValueError("jwt token expired")
    except jwt.InvalidTokenError:
        raise ValueError("invalid token")

def verify_access_token(token:str) ->dict:
   payload = decode_token(token)
   if payload.get("type") != "access":
       raise ValueError("invalid token type")
   return payload  

def verify_refresh_token(token:str)->dict:
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise ValueError("invalid token type")
    return payload
 