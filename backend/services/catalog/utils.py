from os import getenv
from dotenv import load_dotenv
from pathlib import Path
import jwt
from fastapi import Header, HTTPException, status



BASE_DIR =  Path(__file__).resolve().parent

load_dotenv(BASE_DIR/".env")

SECRET_KEY = getenv("SECRET_KEY")

JWT_ALGO = "HS256"

import hashlib

print("CATALOG SECRET LENGTH:", len(SECRET_KEY))
print(
    "CATALOG SECRET HASH:",
    hashlib.sha256(SECRET_KEY.encode()).hexdigest())


def decode_token(token:str)->dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGO])
        print("DECODED PAYLOAD:", payload)
    
        return payload
    # except jwt.ExpiredSignatureError:
    #     raise ValueError("The token has expired. Reauthenticate")

    # except jwt.InvalidTokenError:
    #     raise ValueError("The token is not a valid token")

    except Exception as e:
        print("JWT ERROR:", type(e).__name__, str(e))
        raise

def v_and_d(token:str):

    payload = decode_token(token)
    if payload.get('type')!="access":
        raise ValueError("this token is invalid")
    return payload




def verify_internal_service(
    x_service_key: str = Header(...)
):
    INTERNAL_API_SECRET = getenv("INTERNAL_API_SECRET")
    if x_service_key != INTERNAL_API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service credentials.",
        )

    return True
