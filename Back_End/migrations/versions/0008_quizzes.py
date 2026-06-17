"""quizzes

Revision ID: 0008_quizzes
Revises: 0007_attendance
Create Date: 2026-06-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0008_quizzes"
down_revision = "0007_attendance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "quizzes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("quiz_date", sa.Date(), nullable=False),
        sa.Column("max_grade", sa.Numeric(10, 2), nullable=False),
        sa.Column("source_type", sa.Enum("manual", "csv_upload", name="quizsourcetype", native_enum=False), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["teacher_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quizzes_class_id", "quizzes", ["class_id"], unique=False)
    op.create_index("ix_quizzes_teacher_id", "quizzes", ["teacher_id"], unique=False)
    op.create_index("ix_quizzes_quiz_date", "quizzes", ["quiz_date"], unique=False)
    op.create_index("ix_quizzes_deleted_at", "quizzes", ["deleted_at"], unique=False)
    op.create_index(
        "uq_quizzes_active_identity",
        "quizzes",
        ["class_id", "teacher_id", "title", "quiz_date"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_table(
        "quiz_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quiz_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("earned_grade", sa.Numeric(10, 2), nullable=False),
        sa.Column("max_grade", sa.Numeric(10, 2), nullable=False),
        sa.Column("grade_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["grade_entry_id"], ["grade_entries.id"]),
        sa.ForeignKeyConstraint(["quiz_id"], ["quizzes.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quiz_results_quiz_id", "quiz_results", ["quiz_id"], unique=False)
    op.create_index("ix_quiz_results_student_id", "quiz_results", ["student_id"], unique=False)
    op.create_index("ix_quiz_results_deleted_at", "quiz_results", ["deleted_at"], unique=False)
    op.create_index(
        "uq_quiz_results_active_quiz_student",
        "quiz_results",
        ["quiz_id", "student_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_quiz_results_active_quiz_student", table_name="quiz_results")
    op.drop_index("ix_quiz_results_deleted_at", table_name="quiz_results")
    op.drop_index("ix_quiz_results_student_id", table_name="quiz_results")
    op.drop_index("ix_quiz_results_quiz_id", table_name="quiz_results")
    op.drop_table("quiz_results")
    op.drop_index("uq_quizzes_active_identity", table_name="quizzes")
    op.drop_index("ix_quizzes_deleted_at", table_name="quizzes")
    op.drop_index("ix_quizzes_quiz_date", table_name="quizzes")
    op.drop_index("ix_quizzes_teacher_id", table_name="quizzes")
    op.drop_index("ix_quizzes_class_id", table_name="quizzes")
    op.drop_table("quizzes")
