"""Protected daily learning-plan endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.plan import (
    DailyPlanItemResponse,
    DailyPlanResponse,
    PlanCompletionSummary,
    PlanHistoryItem,
    PlanItemUpdateRequest,
    StreakResponse,
)
from app.services.plan_service import PlanService


router = APIRouter()


@router.get("/today", response_model=DailyPlanResponse)
async def today_plan(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DailyPlanResponse:
    service = PlanService(db)
    return service.serialize_plan(await service.get_or_create_today_plan(str(current_user.id)))


@router.post("/generate", response_model=DailyPlanResponse)
async def regenerate_plan(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DailyPlanResponse:
    service = PlanService(db)
    return service.serialize_plan(await service.generate_today_plan(str(current_user.id), force=True))


@router.get("/history", response_model=list[PlanHistoryItem])
async def plan_history(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PlanHistoryItem]:
    service = PlanService(db)
    return [service.serialize_history(plan) for plan in await service.get_plan_history(str(current_user.id))]


@router.get("/streak", response_model=StreakResponse)
async def streak(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StreakResponse:
    return await PlanService(db).get_streak_info(str(current_user.id))


@router.patch("/items/{item_id}", response_model=DailyPlanItemResponse)
async def update_plan_item(
    item_id: str,
    payload: PlanItemUpdateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DailyPlanItemResponse:
    service = PlanService(db)
    item = await service.update_plan_item_status(
        item_id, str(current_user.id), payload.status, payload.time_spent_minutes
    )
    return service.serialize_item(item)


@router.get("/{plan_id}/summary", response_model=PlanCompletionSummary)
async def completion_summary(
    plan_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlanCompletionSummary:
    return await PlanService(db).get_plan_completion_summary(plan_id, str(current_user.id))


@router.get("/{plan_id}", response_model=DailyPlanResponse)
async def get_plan(
    plan_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DailyPlanResponse:
    service = PlanService(db)
    plan = await service.get_plan_by_id(plan_id, str(current_user.id))
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return service.serialize_plan(plan)
