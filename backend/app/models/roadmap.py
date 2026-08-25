"""Adaptive roadmaps, ordered phases, and actionable roadmap items."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.goal import Goal
    from app.models.learning import DailyPlanItem, LearningSession
    from app.models.skill import Skill
    from app.models.user import User


class Roadmap(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A goal-specific curriculum generated for a learner."""

    __tablename__ = "roadmaps"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    goal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("goals.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    total_phases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_phase_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_generated_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_adapted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped[User] = relationship(back_populates="roadmaps")
    goal: Mapped[Goal] = relationship(back_populates="roadmap")
    phases: Mapped[list[RoadmapPhase]] = relationship(
        back_populates="roadmap", cascade="all, delete-orphan", order_by="RoadmapPhase.order_index"
    )

    def __repr__(self) -> str:
        """Return a concise developer representation."""

        return f"Roadmap(id={self.id!r}, goal_id={self.goal_id!r}, status={self.status!r})"


class RoadmapPhase(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An ordered stage within a learner roadmap."""

    __tablename__ = "roadmap_phases"

    roadmap_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="locked")
    estimated_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    roadmap: Mapped[Roadmap] = relationship(back_populates="phases")
    items: Mapped[list[RoadmapItem]] = relationship(
        back_populates="phase", cascade="all, delete-orphan", order_by="RoadmapItem.order_index"
    )


class RoadmapItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A lesson, exercise, project, assessment, or review in a phase."""

    __tablename__ = "roadmap_items"

    phase_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roadmap_phases.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="SET NULL"), nullable=True
    )
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    phase: Mapped[RoadmapPhase] = relationship(back_populates="items")
    skill: Mapped[Skill | None] = relationship(back_populates="roadmap_items")
    learning_sessions: Mapped[list[LearningSession]] = relationship(
        back_populates="roadmap_item"
    )
    daily_plan_items: Mapped[list[DailyPlanItem]] = relationship(back_populates="roadmap_item")

