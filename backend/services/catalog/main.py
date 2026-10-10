
import logging
import time

from fastapi import FastAPI, Request

from .routes import router as catalog_router
from .logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Catalog Service")


@app.middleware("http")
async def log_request_timing(request: Request, call_next):
    start = time.perf_counter()

    response = await call_next(request)

    elapsed_ms = (time.perf_counter() - start) * 1000

    if request.url.path == "/menu":
        logger.info(
            "REQUEST_TIMING method=%s path=%s status=%s total_ms=%.2f",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )

    return response


app.include_router(catalog_router)
