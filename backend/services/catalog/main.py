import logging
from fastapi import FastAPI
from .routes import router as catalog_router
from .logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Catalog Service")

app.include_router(catalog_router)