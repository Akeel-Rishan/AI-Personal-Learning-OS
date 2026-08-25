"""Reusable exercises and each learner's submitted attempts."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.skill import Skill
    from app.models.user import User


class Exercise(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A skill exercise containing structured prompt data and optional guidance."""

    __tablename__ = "exercises"

    skill_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    exercise_type: Mapped[str] = mapped_column(String(50), nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    content: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    hints: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    skill: Mapped[Skill | None] = relationship(back_populates="exercises")
    attempts: Mapped[list[ExerciseAttempt]] = relationship(
        back_populates="exercise", cascade="all, delete-orphan"
    )


class ExerciseAttempt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A learner submission and its evaluation for an exercise."""

    __tablename__ = "exercise_attempts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False
    )
    user_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    hints_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    user: Mapped[User] = relationship(back_populates="exercise_attempts")
    exercise: Mapped[Exercise] = relationship(back_populates="attempts")

