"""Tutor conversation threads and their ordered messages."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.skill import Skill
    from app.models.user import User


class TutorConversation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A context-preserving AI tutor thread for one learner."""

    __tablename__ = "tutor_conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped[User] = relationship(back_populates="tutor_conversations")
    skill: Mapped[Skill | None] = relationship(back_populates="tutor_conversations")
    messages: Mapped[list[TutorMessage]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="TutorMessage.created_at",
    )


class TutorMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A user, assistant, or system message within a tutor conversation."""

    __tablename__ = "tutor_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tutor_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_metadata: Mapped[dict[str, object] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )

    conversation: Mapped[TutorConversation] = relationship(back_populates="messages")

