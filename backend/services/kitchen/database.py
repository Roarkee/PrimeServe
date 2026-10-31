from typing import Annotated
from sqlmodel import create_engine, Session
from pathlib import Path
from fastapi import Depends
from dotenv import load_dotenv
import os



BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR/".env")

DB_URL = os.getenv("LOCAL_DATABASE_URL")

engine = create_engine(DB_URL,pool_size=5, max_overflow=5,pool_timeout=30,pool_pre_ping=False)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

