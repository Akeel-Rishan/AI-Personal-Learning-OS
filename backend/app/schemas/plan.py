"""Daily learning-plan API schemas."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class DailyPlanItemResponse(BaseModel):
    id: str
    title: str
    description: str | None
    item_type: str
    order_index: int
    estimated_minutes: int
    status: str
    skill_id: str | None
    skill_name: str | None
    roadmap_item_id: str | None
    completed_at: datetime | None

    @field_validator("id", "skill_id", "roadmap_item_id", mode="before")
    @classmethod
    def stringify_ids(cls, value: object) -> str | None:
        return None if value is None else str(value)


class DailyPlanResponse(BaseModel):
    id: str
    plan_date: date
    status: str
    total_estimated_minutes: int
    actual_minutes_spent: int
    ai_generated_note: str | None
    items: list[DailyPlanItemResponse] = Field(default_factory=list)
    completed_items_count: int = 0
    total_items_count: int = 0
    completion_percentage: float = 0.0


class PlanItemUpdateRequest(BaseModel):
    status: Literal["completed", "skipped", "in_progress", "pending"]
    time_spent_minutes: int | None = Field(default=None, ge=0, le=1440)


class PlanCompletionSummary(BaseModel):
    total_items: int
    completed_items: int
    skipped_items: int
    total_minutes_planned: int
    actual_minutes_spent: int
    skills_practiced: list[str]
    xp_earned: int
    streak_days: int
    is_new_streak_milestone: bool
    roadmap_progress_delta: float
    completion_message: str


class PlanHistoryItem(BaseModel):
    id: str
    plan_date: date
    status: str
    completion_percentage: float
    total_minutes_planned: int
    actual_minutes_spent: int
    items_count: int


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    last_completed_date: date | None
    streak_at_risk: bool
