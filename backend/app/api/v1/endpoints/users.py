"""Authenticated user profile preference endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User, UserProfile
from app.schemas.user import UserProfileResponse, UserProfileUpdateRequest


router = APIRouter()


@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    payload: UserProfileUpdateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserProfileResponse:
    profile = await db.scalar(select(UserProfile).where(UserProfile.user_id == current_user.id))
    if profile is None:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
    profile.preferred_explanation_style = payload.preferred_explanation_style
    await db.commit()
    await db.refresh(profile)
    return UserProfileResponse.model_validate(profile)
