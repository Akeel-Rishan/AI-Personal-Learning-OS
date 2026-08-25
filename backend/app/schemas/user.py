"""Public user and profile response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class UserResponse(BaseModel):
    """Safe account fields returned to authenticated clients."""

    id: str
    email: str
    full_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def stringify_id(cls, value: object) -> str:
        """Serialize UUID identifiers consistently as strings."""

        return str(value)


class UserProfileResponse(BaseModel):
    """Learner preferences included with the current-user response."""

    preferred_explanation_style: str
    daily_study_minutes: int
    timezone: str
    avatar_url: str | None

    model_config = ConfigDict(from_attributes=True)


class UserWithProfileResponse(UserResponse):
    """User response enriched with an optional learner profile."""

    profile: UserProfileResponse | None

