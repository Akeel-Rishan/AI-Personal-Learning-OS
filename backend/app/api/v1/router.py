"""Version 1 routes, including service health reporting."""

from typing import Literal, TypedDict

from fastapi import APIRouter


class HealthResponse(TypedDict):
    """Shape returned by the health endpoint."""

    status: Literal["healthy"]
    service: Literal["AI Learning OS"]


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return a lightweight service health response."""

    return {"status": "healthy", "service": "AI Learning OS"}

