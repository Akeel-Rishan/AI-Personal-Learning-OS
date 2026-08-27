"""Version 1 routes, including service health reporting."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.assessments import router as assessments_router
from app.api.v1.endpoints.goals import router as goals_router
from app.api.v1.endpoints.exercises import router as exercises_router
from app.api.v1.endpoints.plans import router as plans_router
from app.api.v1.endpoints.roadmaps import router as roadmaps_router
from app.api.v1.endpoints.skills import router as skills_router
from app.api.v1.endpoints.tutor import router as tutor_router
from app.api.v1.endpoints.users import router as users_router


class HealthResponse(BaseModel):
    """Shape returned by the health endpoint."""

    status: Literal["healthy"]
    service: Literal["AI Learning OS"]


router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(assessments_router, prefix="/assessments", tags=["Assessments"])
router.include_router(goals_router, prefix="/goals", tags=["Goals"])
router.include_router(exercises_router, prefix="/exercises", tags=["Exercises"])
router.include_router(plans_router, prefix="/plans", tags=["Daily Plans"])
router.include_router(roadmaps_router, prefix="/roadmaps", tags=["Roadmaps"])
router.include_router(skills_router, prefix="/skills", tags=["Skills"])
router.include_router(tutor_router, prefix="/tutor", tags=["AI Tutor"])
router.include_router(users_router, prefix="/users", tags=["Users"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return a lightweight service health response."""

    return HealthResponse(status="healthy", service="AI Learning OS")
