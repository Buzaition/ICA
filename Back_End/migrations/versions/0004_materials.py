"""materials

Revision ID: 0004_materials
Revises: 0003_class_enrollments
Create Date: 2026-06-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_materials"
down_revision = "0003_class_enrollments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "materials",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("creator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "creator_role",
            sa.Enum("instructor", "mentor", name="materialcreatorrole", native_enum=False),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "material_type",
            sa.Enum("pdf", "video", "external_file", name="materialtype", native_enum=False),
            nullable=False,
        ),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["creator_id"], ["teacher_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_materials_class_id", "materials", ["class_id"], unique=False)
    op.create_index("ix_materials_creator_id", "materials", ["creator_id"], unique=False)
    op.create_index("ix_materials_material_type", "materials", ["material_type"], unique=False)
    op.create_index("ix_materials_creator_role", "materials", ["creator_role"], unique=False)
    op.create_index("ix_materials_deleted_at", "materials", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_materials_deleted_at", table_name="materials")
    op.drop_index("ix_materials_creator_role", table_name="materials")
    op.drop_index("ix_materials_material_type", table_name="materials")
    op.drop_index("ix_materials_creator_id", table_name="materials")
    op.drop_index("ix_materials_class_id", table_name="materials")
    op.drop_table("materials")
