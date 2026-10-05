import httpx
from dotenv import load_dotenv
from os import getenv

from .schema import (
    CatalogValidationRequest,
    CatalogValidationResponse,
)
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR/".env")

CATALOG_URL = "http://localhost:8001"

CATALOG_API_SECRET=getenv("CATALOG_API_SECRET")
# print("the catalog secret",CATALOG_API_SECRET)



def validate_with_catalog(
    request: CatalogValidationRequest,
) -> CatalogValidationResponse:

    response = httpx.post(
        f"{CATALOG_URL}/menu/validate",
        headers={"X-Service-Key": CATALOG_API_SECRET},
        json=request.model_dump(mode="json"),
        timeout=5.0,
    )

    if response.status_code != 200:
        try:
            detail = response.json().get(
                "detail",
                "Menu validation failed.",
            )
        except ValueError:
            detail = "Menu validation failed."

        raise ValueError(detail)

    return CatalogValidationResponse.model_validate(
        response.json()
    )

