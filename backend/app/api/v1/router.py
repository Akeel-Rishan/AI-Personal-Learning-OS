"""Version 1 routes, including service health reporting."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.v1.endpoints.auth import router as auth_router


class HealthResponse(BaseModel):
    """Shape returned by the health endpoint."""

    status: Literal["healthy"]
    service: Literal["AI Learning OS"]


router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return a lightweight service health response."""

    return HealthResponse(status="healthy", service="AI Learning OS")
