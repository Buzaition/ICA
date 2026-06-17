"""final projects

Revision ID: 0010_final_projects
Revises: 0009_progress_snapshots
Create Date: 2026-06-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0010_final_projects"
down_revision = "0009_progress_snapshots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "final_projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("level_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_link", sa.Text(), nullable=False),
        sa.Column("grade", sa.Numeric(10, 2), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum("pending", "approved", "rejected", name="finalprojectstatus", native_enum=False), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_admin_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["level_id"], ["levels.id"]),
        sa.ForeignKeyConstraint(["reviewed_by_admin_id"], ["admin_profiles.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_final_projects_student_id", "final_projects", ["student_id"], unique=False)
    op.create_index("ix_final_projects_class_id", "final_projects", ["class_id"], unique=False)
    op.create_index("ix_final_projects_level_id", "final_projects", ["level_id"], unique=False)
    op.create_index("ix_final_projects_status", "final_projects", ["status"], unique=False)
    op.create_index("ix_final_projects_deleted_at", "final_projects", ["deleted_at"], unique=False)
    op.create_index(
        "uq_final_projects_active_student_class_level",
        "final_projects",
        ["student_id", "class_id", "level_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_final_projects_active_student_class_level", table_name="final_projects")
    op.drop_index("ix_final_projects_deleted_at", table_name="final_projects")
    op.drop_index("ix_final_projects_status", table_name="final_projects")
    op.drop_index("ix_final_projects_level_id", table_name="final_projects")
    op.drop_index("ix_final_projects_class_id", table_name="final_projects")
    op.drop_index("ix_final_projects_student_id", table_name="final_projects")
    op.drop_table("final_projects")
