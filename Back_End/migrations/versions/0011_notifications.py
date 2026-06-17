"""admin notifications

Revision ID: 0011_notifications
Revises: 0010_final_projects
Create Date: 2026-06-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0011_notifications"
down_revision = "0010_final_projects"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "student_low_progress",
                "instructor_low_progress",
                "mentor_low_progress",
                name="notificationtype",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("target_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_student_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_teacher_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "severity",
            sa.Enum("info", "warning", "critical", name="notificationseverity", native_enum=False),
            nullable=False,
        ),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["target_student_id"], ["student_profiles.id"]),
        sa.ForeignKeyConstraint(["target_teacher_id"], ["teacher_profiles.id"]),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_type", "notifications", ["type"], unique=False)
    op.create_index("ix_notifications_target_user_id", "notifications", ["target_user_id"], unique=False)
    op.create_index("ix_notifications_target_student_id", "notifications", ["target_student_id"], unique=False)
    op.create_index("ix_notifications_target_teacher_id", "notifications", ["target_teacher_id"], unique=False)
    op.create_index("ix_notifications_class_id", "notifications", ["class_id"], unique=False)
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"], unique=False)
    op.create_index("ix_notifications_deleted_at", "notifications", ["deleted_at"], unique=False)
    op.create_index(
        "uq_notifications_unread_target_type_class",
        "notifications",
        ["type", "target_user_id", "target_student_id", "target_teacher_id", "class_id"],
        unique=True,
        postgresql_where=sa.text("is_read = false AND deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_notifications_unread_target_type_class", table_name="notifications")
    op.drop_index("ix_notifications_deleted_at", table_name="notifications")
    op.drop_index("ix_notifications_is_read", table_name="notifications")
    op.drop_index("ix_notifications_class_id", table_name="notifications")
    op.drop_index("ix_notifications_target_teacher_id", table_name="notifications")
    op.drop_index("ix_notifications_target_student_id", table_name="notifications")
    op.drop_index("ix_notifications_target_user_id", table_name="notifications")
    op.drop_index("ix_notifications_type", table_name="notifications")
    op.drop_table("notifications")
