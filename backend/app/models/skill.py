"""Skills, prerequisite graph edges, and skill-owned relationships."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.assessment import AssessmentQuestion
    from app.models.conversation import TutorConversation
    from app.models.exercise import Exercise
    from app.models.goal import GoalSkill
    from app.models.learning import DailyPlanItem, LearningSession
    from app.models.progress import UserSkill
    from app.models.roadmap import RoadmapItem


class Skill(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A reusable unit of knowledge in the learning graph."""

    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    difficulty_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    estimated_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    prerequisite_links: Mapped[list[SkillPrerequisite]] = relationship(
        foreign_keys="SkillPrerequisite.skill_id",
        back_populates="skill",
        cascade="all, delete-orphan",
    )
    dependent_links: Mapped[list[SkillPrerequisite]] = relationship(
        foreign_keys="SkillPrerequisite.prerequisite_id",
        back_populates="prerequisite",
        cascade="all, delete-orphan",
    )
    prerequisites: Mapped[list[Skill]] = relationship(
        secondary="skill_prerequisites",
        primaryjoin="Skill.id == SkillPrerequisite.skill_id",
        secondaryjoin="Skill.id == SkillPrerequisite.prerequisite_id",
        back_populates="dependent_skills",
        viewonly=True,
    )
    dependent_skills: Mapped[list[Skill]] = relationship(
        secondary="skill_prerequisites",
        primaryjoin="Skill.id == SkillPrerequisite.prerequisite_id",
        secondaryjoin="Skill.id == SkillPrerequisite.skill_id",
        back_populates="prerequisites",
        viewonly=True,
    )
    goal_skills: Mapped[list[GoalSkill]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )
    assessment_questions: Mapped[list[AssessmentQuestion]] = relationship(
        back_populates="skill"
    )
    roadmap_items: Mapped[list[RoadmapItem]] = relationship(back_populates="skill")
    learning_sessions: Mapped[list[LearningSession]] = relationship(back_populates="skill")
    daily_plan_items: Mapped[list[DailyPlanItem]] = relationship(back_populates="skill")
    exercises: Mapped[list[Exercise]] = relationship(back_populates="skill")
    user_skills: Mapped[list[UserSkill]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )
    tutor_conversations: Mapped[list[TutorConversation]] = relationship(back_populates="skill")

    def __repr__(self) -> str:
        """Return a concise developer representation."""

        return f"Skill(id={self.id!r}, slug={self.slug!r})"


class SkillPrerequisite(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A directed prerequisite edge between two skills."""

    __tablename__ = "skill_prerequisites"
    __table_args__ = (
        UniqueConstraint(
            "skill_id",
            "prerequisite_id",
            name="uq_skill_prerequisites_skill_prerequisite",
        ),
    )

    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )
    prerequisite_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )
    importance: Mapped[str] = mapped_column(String(20), nullable=False, default="required")

    skill: Mapped[Skill] = relationship(
        foreign_keys=[skill_id], back_populates="prerequisite_links"
    )
    prerequisite: Mapped[Skill] = relationship(
        foreign_keys=[prerequisite_id], back_populates="dependent_links"
    )
