"""Authenticated adaptive exercise and code-review endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.exercise import (
    AttemptFeedbackResponse,
    AttemptRequest,
    CodeReviewRequest,
    CodeReviewResponse,
    ExerciseGenerateRequest,
    ExerciseHistoryItem,
    ExerciseResponse,
    ExerciseStatsResponse,
    ExerciseWithAttemptResponse,
    HintResponse,
    RecommendedExerciseResponse,
)
from app.services.code_review_service import CodeReviewService
from app.services.exercise_service import ExerciseService


router = APIRouter()


@router.get("/recommended", response_model=list[RecommendedExerciseResponse])
async def recommended(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=10)] = 5,
) -> list[RecommendedExerciseResponse]:
    return await ExerciseService(db).get_recommended_exercises(str(current_user.id), limit)


@router.get("/history", response_model=list[ExerciseHistoryItem])
async def history(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skill_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[ExerciseHistoryItem]:
    return await ExerciseService(db).get_exercise_history(str(current_user.id), skill_id, limit)


@router.post("/code-review", response_model=CodeReviewResponse)
async def review_code(
    payload: CodeReviewRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CodeReviewResponse:
    skill_name, mastery = "Python", 0.0
    if payload.skill_id:
        service = ExerciseService(db)
        skill = await service._get_skill(payload.skill_id)
        user_skill = await service._get_user_skill(str(current_user.id), skill.id)
        skill_name, mastery = skill.name, user_skill.mastery_score if user_skill else 0.0
    reviewer = CodeReviewService()
    result = await reviewer.review_free_code(payload.code, payload.context, skill_name, mastery)
    return CodeReviewResponse(**result, formatted=reviewer.format_feedback_for_display(result))


@router.get("/stats/{skill_id}", response_model=ExerciseStatsResponse)
async def stats(
    skill_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ExerciseStatsResponse:
    return await ExerciseService(db).get_skill_exercise_stats(str(current_user.id), skill_id)


@router.get("/skill/{skill_id}", response_model=list[ExerciseWithAttemptResponse])
async def exercises_for_skill(
    skill_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    exclude_completed: bool = True,
) -> list[ExerciseWithAttemptResponse]:
    return await ExerciseService(db).get_exercises_for_skill(skill_id, str(current_user.id), limit, exclude_completed)


@router.post("/generate", response_model=list[ExerciseResponse], status_code=status.HTTP_201_CREATED)
async def generate(
    payload: ExerciseGenerateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ExerciseResponse]:
    service = ExerciseService(db)
    exercises = await service.generate_exercises_for_skill(payload.skill_id, str(current_user.id), payload.count, True, payload.difficulty)
    return [service.serialize_exercise(item) for item in exercises]


@router.get("/{exercise_id}", response_model=ExerciseWithAttemptResponse)
async def get_exercise(
    exercise_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ExerciseWithAttemptResponse:
    exercise = await ExerciseService(db).get_exercise(exercise_id, str(current_user.id))
    if exercise is None:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return exercise


@router.post("/{exercise_id}/attempt", response_model=AttemptFeedbackResponse)
async def submit_attempt(
    exercise_id: str,
    payload: AttemptRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AttemptFeedbackResponse:
    return await ExerciseService(db).submit_attempt(exercise_id, str(current_user.id), payload.user_answer, payload.time_spent_seconds)


@router.get("/{exercise_id}/hint", response_model=HintResponse)
async def get_hint(
    exercise_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    hint_index: Annotated[int, Query(ge=0)] = 0,
) -> HintResponse:
    return await ExerciseService(db).get_hint(exercise_id, str(current_user.id), hint_index)
