"""class enrollments

Revision ID: 0003_class_enrollments
Revises: 0002_academic_structure
Create Date: 2026-06-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_class_enrollments"
down_revision = "0002_academic_structure"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("student_profiles", "status", type_=sa.String(length=9), existing_nullable=False)
    op.create_table(
        "class_enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "completed", "removed", name="enrollmentstatus", native_enum=False),
            nullable=False,
        ),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_class_enrollments_student_id", "class_enrollments", ["student_id"], unique=False)
    op.create_index("ix_class_enrollments_class_id", "class_enrollments", ["class_id"], unique=False)
    op.create_index("ix_class_enrollments_status", "class_enrollments", ["status"], unique=False)
    op.create_index(
        "uq_class_enrollments_one_active_per_student",
        "class_enrollments",
        ["student_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active' AND deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_class_enrollments_one_active_per_student", table_name="class_enrollments")
    op.drop_index("ix_class_enrollments_status", table_name="class_enrollments")
    op.drop_index("ix_class_enrollments_class_id", table_name="class_enrollments")
    op.drop_index("ix_class_enrollments_student_id", table_name="class_enrollments")
    op.drop_table("class_enrollments")
    op.alter_column("student_profiles", "status", type_=sa.String(length=8), existing_nullable=False)
