from typing import Annotated
from sqlmodel import Session,create_engine 
import os
from dotenv import load_dotenv
from fastapi import Depends
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR/".env")

db_url = os.getenv("DB_URL")

engine = create_engine(db_url,pool_size=5,
    max_overflow=5,
    pool_timeout=30,
    pool_pre_ping=False,
    )

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

