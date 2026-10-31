from os import getenv
from dotenv import load_dotenv
from pathlib import Path
import jwt
from fastapi import Header, HTTPException, status



BASE_DIR =  Path(__file__).resolve().parent

load_dotenv(BASE_DIR/".env")

SECRET_KEY = getenv("SECRET_KEY")

JWT_ALGO = getenv('JWT_ALGO')

def verify_decode_token(token:str)->dict:
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[JWT_ALGO])
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except jwt.InvalidSignatureError as e:
        raise HTTPException(status_code=401, detail=str(e))

    if payload.get('type') != 'access':
        raise ValueError("this token is not valid")
    return payload