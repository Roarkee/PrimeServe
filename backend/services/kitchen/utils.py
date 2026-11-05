from os import getenv
from pathlib import Path
import jwt
from fastapi import HTTPException, status
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = getenv("SECRET_KEY", "c337b30891c976933af2f15d664694bb859ac37a148cffa4c028cbc072713ee2")
JWT_ALGO = getenv("JWT_ALGO", "HS256")


def verify_decode_token(token: str) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token or not isinstance(token, str):
        raise credentials_exception

    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[JWT_ALGO])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise credentials_exception

    if not isinstance(payload, dict):
        raise credentials_exception

    if payload.get("type") != "access":
        raise credentials_exception

    if not payload.get("sub"):
        raise credentials_exception

    if not payload.get("restaurant_id"):
        raise credentials_exception

    return payload
