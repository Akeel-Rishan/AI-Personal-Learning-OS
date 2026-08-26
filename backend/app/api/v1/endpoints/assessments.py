"""Protected initial assessment endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.assessment import (
    AnswerFeedbackResponse,
    AnswerSubmitRequest,
    AssessmentCreateRequest,
    AssessmentResultsResponse,
    AssessmentStatusResponse,
)
from app.services.assessment_service import AssessmentService


router = APIRouter()


@router.post("/", response_model=AssessmentStatusResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    payload: AssessmentCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AssessmentStatusResponse:
    assessment = await AssessmentService(db).create_initial_assessment(
        user_id=str(current_user.id),
        goal_id=payload.goal_id,
    )
    return AssessmentService.serialize_status(assessment)


@router.get("/goal/{goal_id}", response_model=AssessmentStatusResponse)
async def get_goal_assessment(
    goal_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AssessmentStatusResponse:
    assessment = await AssessmentService(db).get_by_goal(goal_id, str(current_user.id))
    if assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return AssessmentService.serialize_status(assessment)


@router.get("/{assessment_id}/results", response_model=AssessmentResultsResponse)
async def get_assessment_results(
    assessment_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AssessmentResultsResponse:
    return await AssessmentService(db).get_results(assessment_id, str(current_user.id))


@router.get("/{assessment_id}", response_model=AssessmentStatusResponse)
async def get_assessment(
    assessment_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AssessmentStatusResponse:
    assessment = await AssessmentService(db).get_assessment(assessment_id, str(current_user.id))
    if assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return AssessmentService.serialize_status(assessment)


@router.post("/{assessment_id}/answer", response_model=AnswerFeedbackResponse)
async def submit_answer(
    assessment_id: str,
    payload: AnswerSubmitRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AnswerFeedbackResponse:
    return await AssessmentService(db).submit_answer(
        assessment_id,
        payload.question_id,
        payload.user_answer,
        payload.time_spent_seconds,
        str(current_user.id),
    )
