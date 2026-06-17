"""progress snapshots

Revision ID: 0009_progress_snapshots
Revises: 0008_quizzes
Create Date: 2026-06-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0009_progress_snapshots"
down_revision = "0008_quizzes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "progress_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("attendance_progress", sa.Numeric(10, 2), nullable=False),
        sa.Column("quiz_progress", sa.Numeric(10, 2), nullable=False),
        sa.Column("assignment_progress", sa.Numeric(10, 2), nullable=False),
        sa.Column("bonus_progress", sa.Numeric(10, 2), nullable=False),
        sa.Column("final_progress", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_progress_snapshots_student_id", "progress_snapshots", ["student_id"], unique=False)
    op.create_index("ix_progress_snapshots_class_id", "progress_snapshots", ["class_id"], unique=False)
    op.create_index("ix_progress_snapshots_week_number", "progress_snapshots", ["week_number"], unique=False)
    op.create_index("ix_progress_snapshots_year", "progress_snapshots", ["year"], unique=False)
    op.create_index("ix_progress_snapshots_created_at", "progress_snapshots", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_progress_snapshots_created_at", table_name="progress_snapshots")
    op.drop_index("ix_progress_snapshots_year", table_name="progress_snapshots")
    op.drop_index("ix_progress_snapshots_week_number", table_name="progress_snapshots")
    op.drop_index("ix_progress_snapshots_class_id", table_name="progress_snapshots")
    op.drop_index("ix_progress_snapshots_student_id", table_name="progress_snapshots")
    op.drop_table("progress_snapshots")
