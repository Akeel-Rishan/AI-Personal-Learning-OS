"""Persistent knowledge gaps and the audit trail of adaptive decisions."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, JSON, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.roadmap import Roadmap
    from app.models.skill import Skill
    from app.models.user import User


class AdaptationEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "adaptation_events"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    roadmap_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("roadmaps.id", ondelete="SET NULL"), nullable=True)
    skill_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("skills.id", ondelete="SET NULL"), nullable=True, index=True)
    trigger_type: Mapped[str] = mapped_column(String(100), nullable=False)
    gap_type: Mapped[str] = mapped_column(String(100), nullable=False)
    gap_severity: Mapped[str] = mapped_column(String(20), nullable=False)
    gap_description: Mapped[str] = mapped_column(Text, nullable=False)
    misconception_identified: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_taken: Mapped[str] = mapped_column(String(100), nullable=False)
    action_description: Mapped[str] = mapped_column(Text, nullable=False)
    items_inserted: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_mastery_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship()
    roadmap: Mapped[Roadmap | None] = relationship()
    skill: Mapped[Skill | None] = relationship()


class KnowledgeGap(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_gaps"
    __table_args__ = (
        Index("uq_active_knowledge_gap_user_skill", "user_id", "skill_id", unique=True, postgresql_where=text("status IN ('active','in_progress','acknowledged')")),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    gap_type: Mapped[str] = mapped_column(String(100), nullable=False)
    gap_severity: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    misconception: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    intervention_created: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    intervention_items: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    notification_dismissed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    mastery_at_detection: Mapped[float] = mapped_column(Float, nullable=False)
    mastery_at_resolution: Mapped[float | None] = mapped_column(Float, nullable=True)

    user: Mapped[User] = relationship()
    skill: Mapped[Skill] = relationship()
