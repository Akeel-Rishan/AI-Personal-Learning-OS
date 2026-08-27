"""Authenticated progress analytics endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.progress import ActivityHeatmapDay, CategoryBreakdownItem, LearningVelocityResponse, ProgressSummaryResponse, SkillBreakdownItem, SkillMasteryHistoryPoint, TimeDistributionResponse
from app.services.progress_service import ProgressService


router = APIRouter()


@router.get("/summary", response_model=ProgressSummaryResponse)
async def summary(current_user: Annotated[User, Depends(get_current_active_user)], db: Annotated[AsyncSession, Depends(get_db)]) -> ProgressSummaryResponse:
    return ProgressSummaryResponse(**await ProgressService(db).get_overall_progress_summary(str(current_user.id)))


@router.get("/skills/history", response_model=list[SkillMasteryHistoryPoint])
async def mastery_history(current_user: Annotated[User, Depends(get_current_active_user)], db: Annotated[AsyncSession, Depends(get_db)], skill_id: str | None = None, days: Annotated[int, Query(ge=7, le=365)] = 30) -> list[SkillMasteryHistoryPoint]:
    return [SkillMasteryHistoryPoint(**item) for item in await ProgressService(db).get_skill_mastery_history(str(current_user.id), skill_id, days)]


@router.get("/skills/breakdown", response_model=list[SkillBreakdownItem])
async def skill_breakdown(current_user: Annotated[User, Depends(get_current_active_user)], db: Annotated[AsyncSession, Depends(get_db)]) -> list[SkillBreakdownItem]:
    return [SkillBreakdownItem(**item) for item in await ProgressService(db).get_skill_breakdown_table(str(current_user.id))]


@router.get("/categories", response_model=list[CategoryBreakdownItem])
async def categories(current_user: Annotated[User, Depends(get_current_active_user)], db: Annotated[AsyncSession, Depends(get_db)]) -> list[CategoryBreakdownItem]:
    return [CategoryBreakdownItem(**item) for item in await ProgressService(db).get_skill_category_breakdown(str(current_user.id))]


@router.get("/velocity", response_model=LearningVelocityResponse)
async def velocity(current_user: Annotated[User, Depends(get_current_active_user)], db: Annotated[AsyncSession, Depends(get_db)], period_days: Annotated[int, Query(ge=7, le=90)] = 14) -> LearningVelocityResponse:
    return LearningVelocityResponse(**await ProgressService(db).get_learning_velocity(str(current_user.id), period_days))


@router.get("/heatmap", response_model=list[ActivityHeatmapDay])
async def heatmap(current_user: Annotated[User, Depends(get_current_active_user)], db: Annotated[AsyncSession, Depends(get_db)], weeks: Annotated[int, Query(ge=4, le=52)] = 26) -> list[ActivityHeatmapDay]:
    return [ActivityHeatmapDay(**item) for item in await ProgressService(db).get_activity_heatmap(str(current_user.id), weeks)]


@router.get("/time-distribution", response_model=TimeDistributionResponse)
async def time_distribution(current_user: Annotated[User, Depends(get_current_active_user)], db: Annotated[AsyncSession, Depends(get_db)], days: Annotated[int, Query(ge=7, le=365)] = 30) -> TimeDistributionResponse:
    return TimeDistributionResponse(**await ProgressService(db).get_time_distribution(str(current_user.id), days))
