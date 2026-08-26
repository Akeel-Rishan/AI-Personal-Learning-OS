"""prevent duplicate assessment answers

Revision ID: b57ad102e921
Revises: 8f24b1c9a712
Create Date: 2026-08-26
"""

from collections.abc import Sequence

from alembic import op


revision: str = "b57ad102e921"
down_revision: str | None = "8f24b1c9a712"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_assessment_attempts_assessment_question",
        "assessment_attempts",
        ["assessment_id", "question_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_assessment_attempts_assessment_question",
        "assessment_attempts",
        type_="unique",
    )
