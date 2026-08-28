"""add career mapping tables

Revision ID: f19b7c2d4e60
Revises: e7d3a9b421ce
"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision="f19b7c2d4e60";down_revision="e7d3a9b421ce";branch_labels=None;depends_on=None

def upgrade()->None:
    op.create_table("career_roles",sa.Column("title",sa.String(200),nullable=False),sa.Column("slug",sa.String(200),nullable=False),sa.Column("description",sa.Text(),nullable=False),sa.Column("short_description",sa.String(500),nullable=False),sa.Column("category",sa.String(100),nullable=False),sa.Column("seniority_level",sa.String(50),nullable=False),sa.Column("average_salary_usd",sa.Integer()),sa.Column("demand_level",sa.String(20),nullable=False),sa.Column("typical_companies",sa.JSON(),nullable=False),sa.Column("responsibilities",sa.JSON(),nullable=False),sa.Column("related_role_slugs",sa.JSON(),nullable=False),sa.Column("is_active",sa.Boolean(),nullable=False),sa.Column("is_featured",sa.Boolean(),nullable=False),sa.Column("order_index",sa.Integer(),nullable=False),sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False));op.create_index("ix_career_roles_slug","career_roles",["slug"],unique=True);op.create_index("ix_career_roles_category","career_roles",["category"])
    op.create_table("career_skill_requirements",sa.Column("career_role_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("career_roles.id",ondelete="CASCADE"),nullable=False),sa.Column("skill_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("skills.id",ondelete="CASCADE"),nullable=False),sa.Column("importance",sa.String(20),nullable=False),sa.Column("min_mastery_required",sa.Float(),nullable=False),sa.Column("target_mastery",sa.Float(),nullable=False),sa.Column("relevance_note",sa.String(500)),sa.Column("order_index",sa.Integer(),nullable=False),sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.UniqueConstraint("career_role_id","skill_id",name="uq_career_role_skill"));op.create_index("ix_career_skill_requirements_career_role_id","career_skill_requirements",["career_role_id"]);op.create_index("ix_career_skill_requirements_skill_id","career_skill_requirements",["skill_id"])
    op.create_table("user_career_goals",sa.Column("user_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),sa.Column("career_role_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("career_roles.id",ondelete="CASCADE"),nullable=False),sa.Column("is_primary",sa.Boolean(),nullable=False),sa.Column("initial_readiness",sa.Float()),sa.Column("current_readiness",sa.Float()),sa.Column("target_date",sa.Date()),sa.Column("notes",sa.Text()),sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.UniqueConstraint("user_id","career_role_id",name="uq_user_career_role"));op.create_index("ix_user_career_goals_user_id","user_career_goals",["user_id"]);op.create_index("ix_user_career_goals_career_role_id","user_career_goals",["career_role_id"]);op.create_index("uq_user_primary_career_goal","user_career_goals",["user_id"],unique=True,postgresql_where=sa.text("is_primary"))

def downgrade()->None:
    op.drop_table("user_career_goals");op.drop_table("career_skill_requirements");op.drop_table("career_roles")
