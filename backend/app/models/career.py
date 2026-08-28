"""Career roles, skill requirements, and learner career targets."""
from __future__ import annotations
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.skill import Skill
    from app.models.user import User

class CareerRole(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__="career_roles"
    title:Mapped[str]=mapped_column(String(200),nullable=False);slug:Mapped[str]=mapped_column(String(200),nullable=False,unique=True,index=True);description:Mapped[str]=mapped_column(Text,nullable=False);short_description:Mapped[str]=mapped_column(String(500),nullable=False)
    category:Mapped[str]=mapped_column(String(100),nullable=False,index=True);seniority_level:Mapped[str]=mapped_column(String(50),nullable=False);average_salary_usd:Mapped[int|None]=mapped_column(Integer);demand_level:Mapped[str]=mapped_column(String(20),nullable=False,default="high")
    typical_companies:Mapped[list[str]]=mapped_column(JSON,nullable=False,default=list);responsibilities:Mapped[list[str]]=mapped_column(JSON,nullable=False,default=list);related_role_slugs:Mapped[list[str]]=mapped_column(JSON,nullable=False,default=list)
    is_active:Mapped[bool]=mapped_column(Boolean,nullable=False,default=True);is_featured:Mapped[bool]=mapped_column(Boolean,nullable=False,default=False);order_index:Mapped[int]=mapped_column(Integer,nullable=False,default=0)
    skill_requirements:Mapped[list[CareerSkillRequirement]]=relationship(back_populates="career_role",cascade="all, delete-orphan",order_by="CareerSkillRequirement.order_index");user_career_goals:Mapped[list[UserCareerGoal]]=relationship(back_populates="career_role",cascade="all, delete-orphan")

class CareerSkillRequirement(UUIDPrimaryKeyMixin, Base):
    __tablename__="career_skill_requirements";__table_args__=(UniqueConstraint("career_role_id","skill_id",name="uq_career_role_skill"),)
    career_role_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("career_roles.id",ondelete="CASCADE"),nullable=False,index=True);skill_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("skills.id",ondelete="CASCADE"),nullable=False,index=True)
    importance:Mapped[str]=mapped_column(String(20),nullable=False);min_mastery_required:Mapped[float]=mapped_column(Float,nullable=False);target_mastery:Mapped[float]=mapped_column(Float,nullable=False);relevance_note:Mapped[str|None]=mapped_column(String(500));order_index:Mapped[int]=mapped_column(Integer,nullable=False,default=0);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now())
    career_role:Mapped[CareerRole]=relationship(back_populates="skill_requirements");skill:Mapped[Skill]=relationship()

class UserCareerGoal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__="user_career_goals";__table_args__=(UniqueConstraint("user_id","career_role_id",name="uq_user_career_role"),)
    user_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="CASCADE"),nullable=False,index=True);career_role_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("career_roles.id",ondelete="CASCADE"),nullable=False,index=True)
    is_primary:Mapped[bool]=mapped_column(Boolean,nullable=False,default=True);initial_readiness:Mapped[float|None]=mapped_column(Float);current_readiness:Mapped[float|None]=mapped_column(Float);target_date:Mapped[date|None]=mapped_column(Date);notes:Mapped[str|None]=mapped_column(Text)
    user:Mapped[User]=relationship();career_role:Mapped[CareerRole]=relationship(back_populates="user_career_goals")
