from typing import Annotated
from fastapi import Depends
from sqlmodel import Session, create_engine
from dotenv import load_dotenv
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR/".env")

DB_URL = os.getenv("DB_URL")

engine = create_engine(DB_URL)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
