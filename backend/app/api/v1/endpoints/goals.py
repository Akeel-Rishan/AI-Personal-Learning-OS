"""Authenticated goal creation and roadmap endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.goal import Goal
from app.models.user import User
from app.schemas.goal import (
    GoalCreateRequest,
    GoalDecomposeRequest,
    GoalDecomposeResponse,
    GoalDetailResponse,
    GoalResponse,
    GoalStatusUpdateRequest,
)
from app.services.goal_service import GoalService


router = APIRouter()


def goal_response(goal: Goal) -> GoalResponse:
    """Serialize a goal without triggering lazy relationship loading."""

    return GoalResponse(
        id=str(goal.id),
        user_id=str(goal.user_id),
        title=goal.title,
        description=goal.description,
        target_role=goal.target_role,
        status=goal.status,
        target_date=goal.target_date,
        daily_study_minutes=goal.daily_study_minutes,
        created_at=goal.created_at,
        skill_count=len(goal.__dict__.get("goal_skills", [])),
    )


def goal_detail_response(goal: Goal) -> GoalDetailResponse:
    """Serialize a goal and its eager-loaded generated skill plan."""

    summary = goal_response(goal).model_dump()
    return GoalDetailResponse(
        **summary,
        required_skills=GoalService.serialize_goal_skills(goal),
        ai_summary=goal.ai_summary,
        estimated_weeks=goal.estimated_weeks,
        difficulty_assessment=goal.difficulty_assessment,
        warnings=goal.ai_warnings or [],
    )


@router.post("/", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    payload: GoalCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GoalResponse:
    """Create the learner's new active goal."""

    goal = await GoalService(db).create_goal(str(current_user.id), payload)
    return goal_response(goal)


@router.get("/", response_model=list[GoalResponse])
async def list_goals(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[GoalResponse]:
    """List all goals owned by the current learner."""

    goals = await GoalService(db).get_user_goals(str(current_user.id))
    return [goal_response(goal) for goal in goals]


@router.get("/active", response_model=GoalDetailResponse)
async def active_goal(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GoalDetailResponse:
    """Return the learner's active goal and generated plan."""

    goal = await GoalService(db).get_active_goal(str(current_user.id))
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active goal found")
    return goal_detail_response(goal)


@router.get("/{goal_id}", response_model=GoalDetailResponse)
async def get_goal(
    goal_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GoalDetailResponse:
    """Return one owned goal with its skill graph."""

    goal = await GoalService(db).get_goal_by_id(goal_id, str(current_user.id))
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return goal_detail_response(goal)


@router.post("/{goal_id}/decompose", response_model=GoalDecomposeResponse)
async def decompose_goal(
    goal_id: str,
    payload: GoalDecomposeRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GoalDecomposeResponse:
    """Generate and save a skill plan; model calls commonly take several seconds."""

    if payload.goal_id != goal_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Goal ID does not match route")
    return await GoalService(db).decompose_goal(
        goal_id,
        str(current_user.id),
        payload.existing_knowledge,
    )


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: str,
    payload: GoalCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GoalResponse:
    """Update the editable fields of an owned goal."""

    goal = await GoalService(db).update_goal(goal_id, str(current_user.id), payload)
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return goal_response(goal)


@router.put("/{goal_id}/status", response_model=GoalResponse)
async def update_goal_status(
    goal_id: str,
    payload: GoalStatusUpdateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GoalResponse:
    """Pause, abandon, or reactivate an owned goal."""

    goal = await GoalService(db).update_status(goal_id, str(current_user.id), payload.status)
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return goal_response(goal)
