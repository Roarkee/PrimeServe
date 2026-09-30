from os import getenv
from dotenv import load_dotenv
from pathlib import Path
import jwt

BASE_DIR =  Path(__file__).resolve().parent

load_dotenv(BASE_DIR/".env")

SECRET_KEY = getenv("SECRET_KEY")

JWT_ALGO = "HS256"

def decode_token(token:str)->dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=JWT_ALGO)
    
        return payload
    except jwt.InvalidTokenError:
        raise ValueError("the token is not a valid token")
    except jwt.ExpiredSignatureError:
        raise ValueError("the token has expired. Reauthenticate")

def v_and_d(token:str):

    payload = decode_token(token)
    if payload['type']!="access":
        raise ValueError("this token is invalid")
    return payload
