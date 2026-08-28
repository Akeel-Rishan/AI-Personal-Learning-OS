"""Project templates, staged learner progress, and evaluated submissions."""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.conversation import TutorConversation
    from app.models.user import User

class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__="projects"
    title:Mapped[str]=mapped_column(String(300),nullable=False); slug:Mapped[str]=mapped_column(String(300),nullable=False,unique=True,index=True)
    description:Mapped[str]=mapped_column(Text,nullable=False); short_description:Mapped[str]=mapped_column(String(500),nullable=False)
    difficulty_level:Mapped[int]=mapped_column(Integer,nullable=False,default=1); estimated_hours:Mapped[float]=mapped_column(Float,nullable=False); category:Mapped[str]=mapped_column(String(100),nullable=False,index=True)
    required_skills:Mapped[list[dict[str,object]]]=mapped_column(JSON,nullable=False,default=list); prerequisite_skills:Mapped[list[dict[str,object]]]=mapped_column(JSON,nullable=False,default=list)
    tech_stack:Mapped[list[str]]=mapped_column(JSON,nullable=False,default=list); learning_outcomes:Mapped[list[str]]=mapped_column(JSON,nullable=False,default=list)
    is_active:Mapped[bool]=mapped_column(Boolean,nullable=False,default=True); is_featured:Mapped[bool]=mapped_column(Boolean,nullable=False,default=False); order_index:Mapped[int]=mapped_column(Integer,nullable=False,default=0)
    stages:Mapped[list[ProjectStage]]=relationship(back_populates="project",cascade="all, delete-orphan",order_by="ProjectStage.order_index")
    user_projects:Mapped[list[UserProject]]=relationship(back_populates="project",cascade="all, delete-orphan")

class ProjectStage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__="project_stages"; __table_args__=(UniqueConstraint("project_id","order_index",name="uq_project_stage_order"),)
    project_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("projects.id",ondelete="CASCADE"),nullable=False,index=True)
    title:Mapped[str]=mapped_column(String(300),nullable=False); description:Mapped[str]=mapped_column(Text,nullable=False); order_index:Mapped[int]=mapped_column(Integer,nullable=False)
    stage_type:Mapped[str]=mapped_column(String(50),nullable=False); instructions:Mapped[str]=mapped_column(Text,nullable=False)
    deliverables:Mapped[list[str]]=mapped_column(JSON,nullable=False,default=list); hints:Mapped[list[str]]=mapped_column(JSON,nullable=False,default=list); resources:Mapped[list[dict[str,str]]]=mapped_column(JSON,nullable=False,default=list)
    estimated_minutes:Mapped[int]=mapped_column(Integer,nullable=False,default=30); validation_criteria:Mapped[list[str]]=mapped_column(JSON,nullable=False,default=list)
    project:Mapped[Project]=relationship(back_populates="stages"); user_stages:Mapped[list[UserProjectStage]]=relationship(back_populates="stage",cascade="all, delete-orphan")

class UserProject(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__="user_projects"; __table_args__=(UniqueConstraint("user_id","project_id",name="uq_user_project"),)
    user_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="CASCADE"),nullable=False,index=True); project_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("projects.id",ondelete="CASCADE"),nullable=False,index=True)
    status:Mapped[str]=mapped_column(String(50),nullable=False,default="active"); current_stage_index:Mapped[int]=mapped_column(Integer,nullable=False,default=0); total_stages:Mapped[int]=mapped_column(Integer,nullable=False,default=0)
    work_data:Mapped[dict[str,object]]=mapped_column(JSON,nullable=False,default=dict); xp_earned:Mapped[int]=mapped_column(Integer,nullable=False,default=0)
    final_submission_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True),ForeignKey("project_submissions.id",ondelete="SET NULL",use_alter=True,name="fk_user_project_final_submission"),nullable=True)
    started_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now()); completed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); last_active_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now())
    user:Mapped[User]=relationship(); project:Mapped[Project]=relationship(back_populates="user_projects")
    stage_progress:Mapped[list[UserProjectStage]]=relationship(back_populates="user_project",cascade="all, delete-orphan",order_by="UserProjectStage.stage_order_index")
    submissions:Mapped[list[ProjectSubmission]]=relationship(back_populates="user_project",foreign_keys="ProjectSubmission.user_project_id",cascade="all, delete-orphan")

class UserProjectStage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__="user_project_stages"; __table_args__=(UniqueConstraint("user_project_id","stage_id",name="uq_user_project_stage"),)
    user_project_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("user_projects.id",ondelete="CASCADE"),nullable=False,index=True); stage_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("project_stages.id",ondelete="CASCADE"),nullable=False)
    stage_order_index:Mapped[int]=mapped_column(Integer,nullable=False); status:Mapped[str]=mapped_column(String(50),nullable=False,default="locked")
    submitted_code:Mapped[str|None]=mapped_column(Text); submitted_notes:Mapped[str|None]=mapped_column(Text); submitted_reflection:Mapped[str|None]=mapped_column(Text); submission_hash:Mapped[str|None]=mapped_column(String(64))
    ai_feedback:Mapped[dict[str,object]|None]=mapped_column(JSON); ai_score:Mapped[float|None]=mapped_column(Float); criteria_met:Mapped[list[dict[str,object]]|None]=mapped_column(JSON)
    hints_used:Mapped[int]=mapped_column(Integer,nullable=False,default=0); mentor_conversation_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True),ForeignKey("tutor_conversations.id",ondelete="SET NULL"))
    started_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); submitted_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); completed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
    user_project:Mapped[UserProject]=relationship(back_populates="stage_progress"); stage:Mapped[ProjectStage]=relationship(back_populates="user_stages"); mentor_conversation:Mapped[TutorConversation|None]=relationship()

class ProjectSubmission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__="project_submissions"
    user_project_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("user_projects.id",ondelete="CASCADE"),nullable=False,index=True); user_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="CASCADE"),nullable=False,index=True)
    project_description:Mapped[str]=mapped_column(Text,nullable=False); final_code:Mapped[str|None]=mapped_column(Text); github_url:Mapped[str|None]=mapped_column(String(500)); reflection:Mapped[str|None]=mapped_column(Text); challenges_faced:Mapped[str|None]=mapped_column(Text)
    overall_score:Mapped[float|None]=mapped_column(Float); evaluation_status:Mapped[str]=mapped_column(String(50),nullable=False,default="pending"); ai_evaluation:Mapped[dict[str,object]|None]=mapped_column(JSON); xp_awarded:Mapped[int]=mapped_column(Integer,nullable=False,default=0)
    submitted_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now()); evaluated_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
    user_project:Mapped[UserProject]=relationship(back_populates="submissions",foreign_keys=[user_project_id]); user:Mapped[User]=relationship()
