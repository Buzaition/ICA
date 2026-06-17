"""attendance

Revision ID: 0007_attendance
Revises: 0006_grade_entries
Create Date: 2026-06-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007_attendance"
down_revision = "0006_grade_entries"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "attendance_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "session_type",
            sa.Enum("instructor", "mentor", name="attendancesessiontype", native_enum=False),
            nullable=False,
        ),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("max_grade", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "source_type",
            sa.Enum("manual", "csv_upload", name="attendancesourcetype", native_enum=False),
            nullable=False,
        ),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["teacher_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_attendance_sessions_class_id", "attendance_sessions", ["class_id"], unique=False)
    op.create_index("ix_attendance_sessions_teacher_id", "attendance_sessions", ["teacher_id"], unique=False)
    op.create_index("ix_attendance_sessions_session_date", "attendance_sessions", ["session_date"], unique=False)
    op.create_index("ix_attendance_sessions_session_type", "attendance_sessions", ["session_type"], unique=False)
    op.create_index("ix_attendance_sessions_deleted_at", "attendance_sessions", ["deleted_at"], unique=False)
    op.create_index(
        "uq_attendance_sessions_active_identity",
        "attendance_sessions",
        ["class_id", "teacher_id", "session_type", "session_date"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_table(
        "attendance_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attendance_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum("present", "late", "absent", name="attendancestatus", native_enum=False),
            nullable=False,
        ),
        sa.Column("grade_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["attendance_session_id"], ["attendance_sessions.id"]),
        sa.ForeignKeyConstraint(["grade_entry_id"], ["grade_entries.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_attendance_records_attendance_session_id", "attendance_records", ["attendance_session_id"], unique=False)
    op.create_index("ix_attendance_records_student_id", "attendance_records", ["student_id"], unique=False)
    op.create_index("ix_attendance_records_status", "attendance_records", ["status"], unique=False)
    op.create_index("ix_attendance_records_deleted_at", "attendance_records", ["deleted_at"], unique=False)
    op.create_index(
        "uq_attendance_records_active_session_student",
        "attendance_records",
        ["attendance_session_id", "student_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_attendance_records_active_session_student", table_name="attendance_records")
    op.drop_index("ix_attendance_records_deleted_at", table_name="attendance_records")
    op.drop_index("ix_attendance_records_status", table_name="attendance_records")
    op.drop_index("ix_attendance_records_student_id", table_name="attendance_records")
    op.drop_index("ix_attendance_records_attendance_session_id", table_name="attendance_records")
    op.drop_table("attendance_records")
    op.drop_index("uq_attendance_sessions_active_identity", table_name="attendance_sessions")
    op.drop_index("ix_attendance_sessions_deleted_at", table_name="attendance_sessions")
    op.drop_index("ix_attendance_sessions_session_type", table_name="attendance_sessions")
    op.drop_index("ix_attendance_sessions_session_date", table_name="attendance_sessions")
    op.drop_index("ix_attendance_sessions_teacher_id", table_name="attendance_sessions")
    op.drop_index("ix_attendance_sessions_class_id", table_name="attendance_sessions")
    op.drop_table("attendance_sessions")
