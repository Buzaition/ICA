"""grade entries

Revision ID: 0006_grade_entries
Revises: 0005_assignments
Create Date: 2026-06-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_grade_entries"
down_revision = "0005_assignments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "grade_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "category",
            sa.Enum("assignment", "attendance", "quiz", "bonus", "correction", name="gradecategory", native_enum=False),
            nullable=False,
        ),
        sa.Column("earned_grade", sa.Numeric(10, 2), nullable=False),
        sa.Column("max_grade", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "source_type",
            sa.Enum("manual", "csv_upload", "system_bonus", "correction", name="gradesourcetype", native_enum=False),
            nullable=False,
        ),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("related_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assignment_submission_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assignment_submission_id"], ["assignment_submissions.id"]),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["related_entry_id"], ["grade_entries.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["teacher_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_grade_entries_student_id", "grade_entries", ["student_id"], unique=False)
    op.create_index("ix_grade_entries_class_id", "grade_entries", ["class_id"], unique=False)
    op.create_index("ix_grade_entries_teacher_id", "grade_entries", ["teacher_id"], unique=False)
    op.create_index("ix_grade_entries_category", "grade_entries", ["category"], unique=False)
    op.create_index("ix_grade_entries_source_type", "grade_entries", ["source_type"], unique=False)
    op.create_index("ix_grade_entries_related_entry_id", "grade_entries", ["related_entry_id"], unique=False)
    op.create_index("ix_grade_entries_assignment_submission_id", "grade_entries", ["assignment_submission_id"], unique=False)
    op.create_index("ix_grade_entries_deleted_at", "grade_entries", ["deleted_at"], unique=False)
    op.create_index(
        "uq_grade_entries_assignment_submission_id_active",
        "grade_entries",
        ["assignment_submission_id"],
        unique=True,
        postgresql_where=sa.text("assignment_submission_id IS NOT NULL AND deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_grade_entries_assignment_submission_id_active", table_name="grade_entries")
    op.drop_index("ix_grade_entries_deleted_at", table_name="grade_entries")
    op.drop_index("ix_grade_entries_assignment_submission_id", table_name="grade_entries")
    op.drop_index("ix_grade_entries_related_entry_id", table_name="grade_entries")
    op.drop_index("ix_grade_entries_source_type", table_name="grade_entries")
    op.drop_index("ix_grade_entries_category", table_name="grade_entries")
    op.drop_index("ix_grade_entries_teacher_id", table_name="grade_entries")
    op.drop_index("ix_grade_entries_class_id", table_name="grade_entries")
    op.drop_index("ix_grade_entries_student_id", table_name="grade_entries")
    op.drop_table("grade_entries")
