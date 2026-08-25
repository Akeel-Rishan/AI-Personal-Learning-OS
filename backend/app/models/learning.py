"""Learning sessions and generated daily study plans."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.roadmap import RoadmapItem
    from app.models.skill import Skill
    from app.models.user import User


class LearningSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A timed learner activity associated with a skill or roadmap item."""

    __tablename__ = "learning_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    roadmap_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roadmap_items.id", ondelete="SET NULL"), nullable=True
    )
    skill_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="SET NULL"), nullable=True
    )
    session_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="learning_sessions")
    roadmap_item: Mapped[RoadmapItem | None] = relationship(back_populates="learning_sessions")
    skill: Mapped[Skill | None] = relationship(back_populates="learning_sessions")


class DailyPlan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A unique learner study plan for one calendar date."""

    __tablename__ = "daily_plans"
    __table_args__ = (UniqueConstraint("user_id", "plan_date", name="uq_daily_plans_user_date"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    plan_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    total_estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    actual_minutes_spent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ai_generated_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="daily_plans")
    items: Mapped[list[DailyPlanItem]] = relationship(
        back_populates="daily_plan",
        cascade="all, delete-orphan",
        order_by="DailyPlanItem.order_index",
    )


class DailyPlanItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An ordered task scheduled within a daily plan."""

    __tablename__ = "daily_plan_items"

    daily_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("daily_plans.id", ondelete="CASCADE"), nullable=False
    )
    roadmap_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roadmap_items.id", ondelete="SET NULL"), nullable=True
    )
    skill_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    daily_plan: Mapped[DailyPlan] = relationship(back_populates="items")
    roadmap_item: Mapped[RoadmapItem | None] = relationship(back_populates="daily_plan_items")
    skill: Mapped[Skill | None] = relationship(back_populates="daily_plan_items")

