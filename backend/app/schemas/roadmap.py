"""Personalized roadmap API request and response schemas."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RoadmapItemResponse(BaseModel):
    id: str
    title: str
    description: str | None
    item_type: str
    order_index: int
    status: str
    estimated_minutes: int | None
    skill_id: str | None
    skill_name: str | None
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", "skill_id", mode="before")
    @classmethod
    def stringify_ids(cls, value: object) -> str | None:
        return None if value is None else str(value)


class RoadmapPhaseResponse(BaseModel):
    id: str
    title: str
    description: str | None
    order_index: int
    status: str
    estimated_weeks: int | None
    started_at: datetime | None
    completed_at: datetime | None
    items: list[RoadmapItemResponse] = Field(default_factory=list)
    items_count: int = 0
    completed_items_count: int = 0
    progress_percentage: float = 0.0
    phase_metadata: dict[str, object] | None = None


class RoadmapResponse(BaseModel):
    id: str
    goal_id: str
    goal_title: str
    goal_target_date: date | None = None
    status: str
    total_phases: int
    current_phase_index: int
    estimated_weeks: int | None
    ai_generated_summary: str | None
    phases: list[RoadmapPhaseResponse] = Field(default_factory=list)
    overall_progress_percentage: float = 0.0
    completed_items: int = 0
    total_items: int = 0
    last_adapted_at: datetime | None
    created_at: datetime


class RoadmapGenerateRequest(BaseModel):
    goal_id: str


class RoadmapItemUpdateRequest(BaseModel):
    status: Literal["completed", "skipped", "pending", "active"]


class RoadmapItemUpdateResponse(BaseModel):
    item: RoadmapItemResponse
    phase_id: str
    phase_status: str
    phase_progress_percentage: float
    roadmap_progress_percentage: float
    unlocked_phase_id: str | None = None


class PhaseUnlockRequest(BaseModel):
    phase_id: str


class PhaseProgressResponse(BaseModel):
    phase_id: str
    title: str
    progress: float
    status: str


class RoadmapProgressResponse(BaseModel):
    total_items: int
    completed_items: int
    overall_percentage: float
    current_phase: str | None
    estimated_completion_date: date | None
    phases: list[PhaseProgressResponse]
