from fastapi import FastAPI
from .routes import router as catalog_router

app = FastAPI(title="Catalog Service")

app.include_router(catalog_router)