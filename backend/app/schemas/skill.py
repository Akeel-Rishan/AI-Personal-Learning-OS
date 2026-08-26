"""Skill graph API schemas."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SkillResponse(BaseModel):
    """Public skill metadata."""

    id: str
    name: str
    slug: str
    description: str | None
    category: str
    difficulty_level: int
    estimated_hours: float | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def stringify_id(cls, value: object) -> str:
        return str(value)


class SkillWithPrerequisitesResponse(SkillResponse):
    """Skill metadata plus its direct prerequisite skills."""

    prerequisites: list[SkillResponse] = Field(default_factory=list)


class SkillPrerequisiteResponse(BaseModel):
    """A prerequisite edge and its importance."""

    skill: SkillResponse
    importance: str


class SkillCategoryResponse(BaseModel):
    """Skill count for one category."""

    category: str
    count: int
