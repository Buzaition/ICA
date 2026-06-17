"""assignments and submissions

Revision ID: 0005_assignments
Revises: 0004_materials
Create Date: 2026-06-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_assignments"
down_revision = "0004_materials"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("requirement_url", sa.Text(), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("max_grade", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["created_by_teacher_id"], ["teacher_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assignments_class_id", "assignments", ["class_id"], unique=False)
    op.create_index("ix_assignments_created_by_teacher_id", "assignments", ["created_by_teacher_id"], unique=False)
    op.create_index("ix_assignments_deadline", "assignments", ["deadline"], unique=False)
    op.create_index("ix_assignments_deleted_at", "assignments", ["deleted_at"], unique=False)

    op.create_table(
        "assignment_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("submission_url", sa.Text(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("grade", sa.Numeric(10, 2), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("submitted", "reviewed", "late", "replaced", "rejected", name="assignmentsubmissionstatus", native_enum=False),
            nullable=False,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_teacher_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"]),
        sa.ForeignKeyConstraint(["reviewed_by_teacher_id"], ["teacher_profiles.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assignment_submissions_assignment_id", "assignment_submissions", ["assignment_id"], unique=False)
    op.create_index("ix_assignment_submissions_student_id", "assignment_submissions", ["student_id"], unique=False)
    op.create_index("ix_assignment_submissions_status", "assignment_submissions", ["status"], unique=False)
    op.create_index("ix_assignment_submissions_reviewed_at", "assignment_submissions", ["reviewed_at"], unique=False)
    op.create_index("ix_assignment_submissions_deleted_at", "assignment_submissions", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_assignment_submissions_deleted_at", table_name="assignment_submissions")
    op.drop_index("ix_assignment_submissions_reviewed_at", table_name="assignment_submissions")
    op.drop_index("ix_assignment_submissions_status", table_name="assignment_submissions")
    op.drop_index("ix_assignment_submissions_student_id", table_name="assignment_submissions")
    op.drop_index("ix_assignment_submissions_assignment_id", table_name="assignment_submissions")
    op.drop_table("assignment_submissions")
    op.drop_index("ix_assignments_deleted_at", table_name="assignments")
    op.drop_index("ix_assignments_deadline", table_name="assignments")
    op.drop_index("ix_assignments_created_by_teacher_id", table_name="assignments")
    op.drop_index("ix_assignments_class_id", table_name="assignments")
    op.drop_table("assignments")
