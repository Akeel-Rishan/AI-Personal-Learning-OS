"""Assessments, generated questions, and learner attempts."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.goal import Goal
    from app.models.skill import Skill
    from app.models.user import User


class Assessment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A diagnostic or mastery evaluation for a learner."""

    __tablename__ = "assessments"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    goal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("goals.id", ondelete="SET NULL"), nullable=True
    )
    assessment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="assessments")
    goal: Mapped[Goal | None] = relationship(back_populates="assessments")
    questions: Mapped[list[AssessmentQuestion]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )
    attempts: Mapped[list[AssessmentAttempt]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )


class AssessmentQuestion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single question belonging to an assessment."""

    __tablename__ = "assessment_questions"

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="SET NULL"), nullable=True
    )
    question_type: Mapped[str] = mapped_column(String(50), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    assessment: Mapped[Assessment] = relationship(back_populates="questions")
    skill: Mapped[Skill | None] = relationship(back_populates="assessment_questions")
    attempts: Mapped[list[AssessmentAttempt]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )


class AssessmentAttempt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A learner's answer and evaluation for one assessment question."""

    __tablename__ = "assessment_attempts"

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessment_questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    assessment: Mapped[Assessment] = relationship(back_populates="attempts")
    question: Mapped[AssessmentQuestion] = relationship(back_populates="attempts")

