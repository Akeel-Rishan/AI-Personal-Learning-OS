"""Career-role discovery, readiness, comparison, and goal routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.career import (
    ActionPlanResponse,
    CareerCompareRequest,
    CareerGoalSetRequest,
    CareerReadinessResponse,
    CareerRoleResponse,
    MarketInsightsResponse,
)
from app.services.career_service import CareerService

router = APIRouter()
CurrentUser = Annotated[User, Depends(get_current_active_user)]
Database = Annotated[AsyncSession, Depends(get_db)]


@router.get("/roles", response_model=list[CareerRoleResponse])
async def list_roles(current_user: CurrentUser, db: Database, category: str | None = None) -> list[dict[str, object]]:
    service = CareerService(db)
    return [service.serialize_role(role) for role in await service.get_all_roles(category)]


@router.get("/roles/categories")
async def role_categories(current_user: CurrentUser, db: Database) -> list[dict[str, object]]:
    return await CareerService(db).get_role_categories()


@router.post("/compare", response_model=list[CareerReadinessResponse])
async def compare_roles(payload: CareerCompareRequest, current_user: CurrentUser, db: Database) -> list[dict[str, object]]:
    if len(set(payload.role_ids)) != len(payload.role_ids):
        raise HTTPException(status_code=422, detail="Choose different roles to compare")
    return await CareerService(db).compare_roles(str(current_user.id), payload.role_ids)


@router.post("/goal")
async def set_goal(payload: CareerGoalSetRequest, current_user: CurrentUser, db: Database) -> dict[str, object]:
    return await CareerService(db).set_primary_career_goal(
        str(current_user.id), payload.role_id, payload.target_date, payload.job_ready_alert
    )


@router.get("/goal")
async def get_goal(current_user: CurrentUser, db: Database, response: Response) -> dict[str, object] | None:
    result = await CareerService(db).get_primary_career_goal(str(current_user.id))
    if result is None:
        response.status_code = status.HTTP_204_NO_CONTENT
    return result


@router.delete("/goal")
async def delete_goal(current_user: CurrentUser, db: Database) -> dict[str, bool]:
    await CareerService(db).remove_primary_goal(str(current_user.id))
    return {"removed": True}


@router.get("/roles/{role_id}/readiness", response_model=CareerReadinessResponse)
async def role_readiness(role_id: str, current_user: CurrentUser, db: Database) -> dict[str, object]:
    return await CareerService(db).calculate_career_readiness(str(current_user.id), role_id)


@router.get("/roles/{role_id}/action-plan", response_model=ActionPlanResponse)
async def action_plan(role_id: str, current_user: CurrentUser, db: Database) -> dict[str, object]:
    return await CareerService(db).generate_action_plan(str(current_user.id), role_id)


@router.get("/roles/{role_id}/market-insights", response_model=MarketInsightsResponse)
async def market_insights(role_id: str, current_user: CurrentUser, db: Database) -> dict[str, object]:
    return await CareerService(db).get_market_insights(role_id)


@router.get("/roles/{role_slug}", response_model=CareerRoleResponse)
async def role_detail(role_slug: str, current_user: CurrentUser, db: Database) -> dict[str, object]:
    service = CareerService(db)
    role = await service.get_role_by_slug(role_slug)
    if role is None:
        raise HTTPException(status_code=404, detail="Career role not found")
    return service.serialize_role(role)
