"""Progress analytics response schemas."""

from datetime import date

from pydantic import BaseModel, Field


class SkillMasteryHistoryPoint(BaseModel):
    date: date
    skill_id: str | None
    skill_name: str | None
    mastery_score: float
    mastery_percentage: int


class ProgressSummaryResponse(BaseModel):
    total_skills_tracked: int
    skills_mastered: int
    skills_in_progress: int
    skills_not_started: int
    average_mastery: float
    strongest_skill: dict[str, object] | None
    weakest_skill: dict[str, object] | None
    total_study_minutes: int
    total_exercises_completed: int
    total_assessments_completed: int
    roadmap_progress: float
    days_learning: int
    active_days: int
    current_streak: int
    longest_streak: int


class LearningVelocityResponse(BaseModel):
    mastery_gained_this_period: float
    mastery_per_active_day: float
    active_days_this_period: int
    exercises_per_day: float
    minutes_per_day: float
    velocity_trend: str
    velocity_vs_last_period: float
    estimated_goal_completion_weeks: int | None


class CategoryBreakdownItem(BaseModel):
    category: str
    average_mastery: float
    mastery_percentage: int
    skills_count: int
    skills_mastered: int
    skills: list[dict[str, object]] = Field(default_factory=list)


class ActivityHeatmapDay(BaseModel):
    date: date
    completed_items: int
    study_minutes: int
    intensity: int


class SkillBreakdownItem(BaseModel):
    skill_id: str
    skill_name: str
    skill_slug: str
    category: str
    mastery_score: float
    mastery_percentage: int
    mastery_level: str
    times_practiced: int
    times_correct: int
    accuracy_rate: float
    last_practiced_days_ago: int | None
    mastery_7d_change: float
    mastery_trend: str
    review_due: bool = False


class TimeDistributionResponse(BaseModel):
    by_hour: list[dict[str, object]]
    by_day_of_week: list[dict[str, object]]
    peak_study_hour: int
    peak_study_day: str
    morning_learner: bool
    average_session_minutes: float
    longest_session_minutes: int
    grid: list[dict[str, object]]
