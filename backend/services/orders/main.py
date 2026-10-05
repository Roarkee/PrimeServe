from fastapi import FastAPI
from .routes import router as order_router

app = FastAPI(title="Order Service")

app.include_router(order_router)