"""add goal AI decomposition metadata

Revision ID: 8f24b1c9a712
Revises: dbe37ee03636
Create Date: 2026-08-25
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "8f24b1c9a712"
down_revision: str | None = "dbe37ee03636"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Persist goal-planning input and AI decomposition output."""

    op.add_column("goals", sa.Column("existing_knowledge", sa.Text(), nullable=False, server_default=""))
    op.add_column("goals", sa.Column("ai_summary", sa.Text(), nullable=True))
    op.add_column("goals", sa.Column("estimated_weeks", sa.Integer(), nullable=True))
    op.add_column("goals", sa.Column("difficulty_assessment", sa.String(length=50), nullable=True))
    op.add_column("goals", sa.Column("ai_warnings", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("goal_skills", sa.Column("reason", sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove goal-planning metadata."""

    op.drop_column("goal_skills", "reason")
    op.drop_column("goals", "ai_warnings")
    op.drop_column("goals", "difficulty_assessment")
    op.drop_column("goals", "estimated_weeks")
    op.drop_column("goals", "ai_summary")
    op.drop_column("goals", "existing_knowledge")
