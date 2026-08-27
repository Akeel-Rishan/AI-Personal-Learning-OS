"""XP, level, achievement, streak, and leaderboard schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class LevelInfo(BaseModel):
    level: int
    total_xp: int
    xp_for_current_level: int
    xp_for_next_level: int
    xp_progress: int
    xp_needed: int
    progress_percentage: float
    level_title: str


class XPEventResponse(BaseModel):
    event_type: str
    xp_earned: int
    description: str | None
    created_at: datetime


class XPSummaryResponse(LevelInfo):
    xp_breakdown: dict[str, int]
    recent_xp_events: list[XPEventResponse] = Field(default_factory=list)


class XPHistoryDay(BaseModel):
    date: date
    xp_earned: int
    events_count: int


class AchievementResponse(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    achievement_type: str
    xp_reward: int
    earned_at: datetime | None = None
    progress: float | None = None
    progress_label: str | None = None


class AchievementsResponse(BaseModel):
    earned: list[AchievementResponse]
    locked: list[AchievementResponse]
    total_earned: int
    total_available: int
    completion_percentage: float


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    streak_start_date: date | None
    last_activity_date: date | None
    streak_at_risk: bool
    streak_frozen: bool = False
    milestone_next: int
    days_to_milestone: int


class LeaderboardEntry(BaseModel):
    rank: int
    user_name: str
    level: int
    total_xp: int
    streak: int
    is_current_user: bool


class LevelUpResponse(BaseModel):
    leveled_up: bool
    old_level: int
    new_level: int
    new_title: str
    bonus_xp: int
