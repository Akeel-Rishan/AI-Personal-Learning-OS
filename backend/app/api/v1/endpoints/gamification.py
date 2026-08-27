"""Authenticated XP, achievement, streak, and leaderboard endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.gamification import AchievementResponse, AchievementsResponse, LeaderboardEntry, StreakResponse, XPHistoryDay, XPSummaryResponse
from app.services.gamification_service import GamificationService


router = APIRouter()


@router.get("/xp", response_model=XPSummaryResponse)
async def xp_summary(current_user: Annotated[User, Depends(get_current_active_user)], db: Annotated[AsyncSession, Depends(get_db)]) -> XPSummaryResponse:
    return XPSummaryResponse(**await GamificationService(db).get_user_xp_summary(str(current_user.id)))


@router.get("/xp/history", response_model=list[XPHistoryDay])
async def xp_history(current_user: Annotated[User, Depends(get_current_active_user)], db: Annotated[AsyncSession, Depends(get_db)], days: Annotated[int, Query(ge=7, le=365)] = 30) -> list[XPHistoryDay]:
    return [XPHistoryDay(**item) for item in await GamificationService(db).get_xp_history(str(current_user.id), days)]


@router.get("/achievements", response_model=AchievementsResponse)
async def achievements(current_user: Annotated[User, Depends(get_current_active_user)], db: Annotated[AsyncSession, Depends(get_db)]) -> AchievementsResponse:
    return AchievementsResponse(**await GamificationService(db).get_user_achievements(str(current_user.id)))


@router.post("/achievements/check", response_model=list[AchievementResponse])
async def check_achievements(current_user: Annotated[User, Depends(get_current_active_user)], db: Annotated[AsyncSession, Depends(get_db)]) -> list[AchievementResponse]:
    service = GamificationService(db); awarded = await service.check_and_award_achievements(str(current_user.id)); await db.commit()
    return [AchievementResponse(id=str(item.achievement.id), name=item.achievement.name, description=item.achievement.description, icon=item.achievement.icon or "🏅", achievement_type=item.achievement.achievement_type, xp_reward=item.achievement.xp_reward, earned_at=item.earned_at, progress=1, progress_label="Completed") for item in awarded]


@router.get("/streak", response_model=StreakResponse)
async def streak(current_user: Annotated[User, Depends(get_current_active_user)], db: Annotated[AsyncSession, Depends(get_db)]) -> StreakResponse:
    return StreakResponse(**await GamificationService(db).get_streak_info(str(current_user.id)))


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def leaderboard(current_user: Annotated[User, Depends(get_current_active_user)], db: Annotated[AsyncSession, Depends(get_db)]) -> list[LeaderboardEntry]:
    return [LeaderboardEntry(**item) for item in await GamificationService(db).get_leaderboard(str(current_user.id))]
