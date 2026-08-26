"""Learner goals and the skills required to achieve them."""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, Date, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.assessment import Assessment
    from app.models.roadmap import Roadmap
    from app.models.skill import Skill
    from app.models.user import User


class Goal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A learner's desired outcome and study commitment."""

    __tablename__ = "goals"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_role: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    daily_study_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    existing_knowledge: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty_assessment: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_warnings: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    user: Mapped[User] = relationship(back_populates="goals")
    goal_skills: Mapped[list[GoalSkill]] = relationship(
        back_populates="goal", cascade="all, delete-orphan"
    )
    roadmap: Mapped[Roadmap | None] = relationship(
        back_populates="goal", cascade="all, delete-orphan", uselist=False
    )
    assessments: Mapped[list[Assessment]] = relationship(back_populates="goal")

    def __repr__(self) -> str:
        """Return a concise developer representation."""

        return f"Goal(id={self.id!r}, title={self.title!r}, status={self.status!r})"


class GoalSkill(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An ordered skill requirement attached to a learner goal."""

    __tablename__ = "goal_skills"
    __table_args__ = (UniqueConstraint("goal_id", "skill_id", name="uq_goal_skills_goal_skill"),)

    goal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )
    priority_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    goal: Mapped[Goal] = relationship(back_populates="goal_skills")
    skill: Mapped[Skill] = relationship(back_populates="goal_skills")
