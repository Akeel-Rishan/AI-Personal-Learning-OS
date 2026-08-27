"""add adaptive learning tables

Revision ID: c4a9d81e2f10
Revises: b57ad102e921
Create Date: 2026-08-27
"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c4a9d81e2f10"
down_revision: str | None = "b57ad102e921"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.add_column("roadmap_phases", sa.Column("metadata", sa.JSON(), nullable=True))
    op.create_table("knowledge_gaps",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gap_type", sa.String(100), nullable=False), sa.Column("gap_severity", sa.String(20), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("misconception", sa.Text(), nullable=True), sa.Column("evidence", sa.JSON(), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("intervention_created", sa.Boolean(), nullable=False), sa.Column("intervention_items", sa.JSON(), nullable=True), sa.Column("notification_dismissed", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True), sa.Column("mastery_at_detection", sa.Float(), nullable=False), sa.Column("mastery_at_resolution", sa.Float(), nullable=True), sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["skill_id"],["skills.id"],ondelete="CASCADE"), sa.ForeignKeyConstraint(["user_id"],["users.id"],ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_knowledge_gaps_user_id", "knowledge_gaps", ["user_id"]); op.create_index("ix_knowledge_gaps_skill_id", "knowledge_gaps", ["skill_id"])
    op.create_index("uq_active_knowledge_gap_user_skill", "knowledge_gaps", ["user_id", "skill_id"], unique=True, postgresql_where=sa.text("status IN ('active','in_progress','acknowledged')"))
    op.create_table("adaptation_events",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("roadmap_id", postgresql.UUID(as_uuid=True), nullable=True), sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=True), sa.Column("trigger_type", sa.String(100), nullable=False), sa.Column("gap_type", sa.String(100), nullable=False), sa.Column("gap_severity", sa.String(20), nullable=False), sa.Column("gap_description", sa.Text(), nullable=False), sa.Column("misconception_identified", sa.Text(), nullable=True), sa.Column("action_taken", sa.String(100), nullable=False), sa.Column("action_description", sa.Text(), nullable=False), sa.Column("items_inserted", sa.JSON(), nullable=True), sa.Column("is_resolved", sa.Boolean(), nullable=False), sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True), sa.Column("resolution_mastery_score", sa.Float(), nullable=True), sa.Column("ai_reasoning", sa.Text(), nullable=True), sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["roadmap_id"],["roadmaps.id"],ondelete="SET NULL"), sa.ForeignKeyConstraint(["skill_id"],["skills.id"],ondelete="SET NULL"), sa.ForeignKeyConstraint(["user_id"],["users.id"],ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_adaptation_events_user_id", "adaptation_events", ["user_id"]); op.create_index("ix_adaptation_events_skill_id", "adaptation_events", ["skill_id"])

def downgrade() -> None:
    op.drop_index("ix_adaptation_events_skill_id", table_name="adaptation_events"); op.drop_index("ix_adaptation_events_user_id", table_name="adaptation_events"); op.drop_table("adaptation_events")
    op.drop_index("uq_active_knowledge_gap_user_skill", table_name="knowledge_gaps"); op.drop_index("ix_knowledge_gaps_skill_id", table_name="knowledge_gaps"); op.drop_index("ix_knowledge_gaps_user_id", table_name="knowledge_gaps"); op.drop_table("knowledge_gaps"); op.drop_column("roadmap_phases", "metadata")
