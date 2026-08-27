"""Protected personalized roadmap endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.roadmap import (
    RoadmapGenerateRequest,
    RoadmapItemUpdateRequest,
    RoadmapItemUpdateResponse,
    RoadmapProgressResponse,
    RoadmapResponse,
)
from app.services.roadmap_service import RoadmapService


router = APIRouter()


@router.post("/generate", response_model=RoadmapResponse, status_code=status.HTTP_201_CREATED)
async def generate_roadmap(
    payload: RoadmapGenerateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoadmapResponse:
    service = RoadmapService(db)
    roadmap = await service.generate_roadmap(str(current_user.id), payload.goal_id)
    return service.serialize_roadmap(roadmap)


@router.get("/goal/{goal_id}", response_model=RoadmapResponse)
async def get_goal_roadmap(
    goal_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoadmapResponse:
    service = RoadmapService(db)
    roadmap = await service.get_roadmap_by_goal(goal_id, str(current_user.id))
    if roadmap is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")
    return service.serialize_roadmap(roadmap)


@router.patch("/items/{item_id}", response_model=RoadmapItemUpdateResponse)
async def update_roadmap_item(
    item_id: str,
    payload: RoadmapItemUpdateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoadmapItemUpdateResponse:
    return await RoadmapService(db).update_item_status(item_id, str(current_user.id), payload.status)


@router.get("/{roadmap_id}/progress", response_model=RoadmapProgressResponse)
async def get_roadmap_progress(
    roadmap_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoadmapProgressResponse:
    return await RoadmapService(db).calculate_roadmap_progress(roadmap_id, str(current_user.id))


@router.post("/{roadmap_id}/adapt", response_model=RoadmapResponse)
async def adapt_roadmap(
    roadmap_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoadmapResponse:
    service = RoadmapService(db)
    roadmap = await service.adapt_roadmap(roadmap_id, str(current_user.id))
    return service.serialize_roadmap(roadmap)


@router.get("/{roadmap_id}", response_model=RoadmapResponse)
async def get_roadmap(
    roadmap_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoadmapResponse:
    service = RoadmapService(db)
    roadmap = await service.get_roadmap_by_id(roadmap_id, str(current_user.id))
    if roadmap is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")
    return service.serialize_roadmap(roadmap)
