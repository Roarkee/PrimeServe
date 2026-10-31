from fastapi import FastAPI
from .routes import kitchen_router, internal_router

app = FastAPI(title= "PrimeServe Kitchen Service")

app.include_router(kitchen_router)
app.include_router(internal_router)