"""User accounts, learner profiles, and their top-level relationships."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.assessment import Assessment
    from app.models.conversation import TutorConversation
    from app.models.exercise import ExerciseAttempt
    from app.models.gamification import UserAchievement, XPEvent
    from app.models.goal import Goal
    from app.models.learning import DailyPlan, LearningSession
    from app.models.progress import UserSkill
    from app.models.roadmap import Roadmap


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A learner account and the root owner of personalized learning data."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    profile: Mapped[UserProfile | None] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    goals: Mapped[list[Goal]] = relationship(back_populates="user", cascade="all, delete-orphan")
    assessments: Mapped[list[Assessment]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    roadmaps: Mapped[list[Roadmap]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    user_skills: Mapped[list[UserSkill]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    learning_sessions: Mapped[list[LearningSession]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    daily_plans: Mapped[list[DailyPlan]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    exercise_attempts: Mapped[list[ExerciseAttempt]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    tutor_conversations: Mapped[list[TutorConversation]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    achievements: Mapped[list[UserAchievement]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    xp_events: Mapped[list[XPEvent]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """Return a concise developer representation."""

        return f"User(id={self.id!r}, email={self.email!r})"


class UserProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A learner's preferences and public profile information."""

    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    preferred_explanation_style: Mapped[str] = mapped_column(
        String(50), nullable=False, default="balanced"
    )
    daily_study_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    timezone: Mapped[str] = mapped_column(String(100), nullable=False, default="UTC")
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="profile")

