"""Version 1 routes, including service health reporting."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Shape returned by the health endpoint."""

    status: Literal["healthy"]
    service: Literal["AI Learning OS"]


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return a lightweight service health response."""

    return HealthResponse(status="healthy", service="AI Learning OS")
