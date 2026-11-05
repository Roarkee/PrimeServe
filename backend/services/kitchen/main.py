from fastapi import FastAPI
from .routes.routes import kitchen_router, internal_router
from .routes.websocket_route import router as websocket_router

app = FastAPI(title="PrimeServe Kitchen Service")

app.include_router(kitchen_router)
app.include_router(internal_router)
app.include_router(websocket_router)