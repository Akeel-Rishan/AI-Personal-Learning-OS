"""Goal planning request and response schemas."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.skill import SkillWithPrerequisitesResponse


class GoalCreateRequest(BaseModel):
    """Validated input for a learner goal."""

    title: str = Field(min_length=10, max_length=300)
    description: str | None = Field(default=None, max_length=2000)
    target_role: str | None = Field(default=None, max_length=200)
    daily_study_minutes: int = Field(ge=15, le=480)
    target_date: date | None = None
    existing_knowledge: str = Field(default="", max_length=3000)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 10:
            raise ValueError("Goal title must contain at least 10 characters")
        return cleaned


class GoalResponse(BaseModel):
    """Goal summary returned in lists and mutations."""

    id: str
    user_id: str
    title: str
    description: str | None
    target_role: str | None
    status: str
    target_date: date | None
    daily_study_minutes: int
    created_at: datetime
    skill_count: int = 0

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", "user_id", mode="before")
    @classmethod
    def stringify_ids(cls, value: object) -> str:
        return str(value)


class GoalSkillResponse(BaseModel):
    """One ordered skill requirement in a goal plan."""

    skill: SkillWithPrerequisitesResponse
    priority_order: int
    is_required: bool
    reason: str | None = None


class GoalDetailResponse(GoalResponse):
    """Goal summary enriched with its generated plan."""

    required_skills: list[GoalSkillResponse] = Field(default_factory=list)
    ai_summary: str | None = None
    estimated_weeks: int | None = None
    difficulty_assessment: str | None = None
    warnings: list[str] = Field(default_factory=list)


class GoalDecomposeRequest(BaseModel):
    """Input for an authenticated goal decomposition."""

    goal_id: str
    existing_knowledge: str = Field(default="", max_length=3000)


class GoalDecomposeResponse(BaseModel):
    """Persisted AI-generated goal plan."""

    goal_id: str
    required_skills: list[GoalSkillResponse]
    estimated_weeks: int
    difficulty_assessment: str
    summary: str
    recommended_daily_focus_minutes: int
    warnings: list[str] = Field(default_factory=list)
    note: str = "AI decomposition completed and saved to this goal."


class GoalStatusUpdateRequest(BaseModel):
    """Allowed goal lifecycle transition."""

    status: Literal["active", "paused", "abandoned"]
