"""academic structure

Revision ID: 0002_academic_structure
Revises: 0001_initial
Create Date: 2026-06-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_academic_structure"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "branches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "cycles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cycle_number", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.Enum("active", "closed", name="cyclestatus", native_enum=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cycle_number"),
    )
    op.create_table(
        "tracks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=2), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("track_number", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("track_number"),
    )
    op.create_table(
        "levels",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("track_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("level_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("duration_months", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("level_number IN (1, 2, 3)", name="ck_levels_level_number_range"),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("track_id", "level_number", name="uq_levels_track_id_level_number"),
    )
    op.create_table(
        "classes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=6), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cycle_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("track_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("level_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instructor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mentor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("schedule_text", sa.Text(), nullable=False),
        sa.Column("max_students", sa.Integer(), nullable=False),
        sa.Column("class_type", sa.Enum("onsite", "online", name="classtype", native_enum=False), nullable=False),
        sa.Column(
            "status",
            sa.Enum("planned", "active", "completed", "cancelled", name="classstatus", native_enum=False),
            nullable=False,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("max_students <= 25", name="ck_classes_max_students_limit"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["cycle_id"], ["cycles.id"]),
        sa.ForeignKeyConstraint(["instructor_id"], ["teacher_profiles.id"]),
        sa.ForeignKeyConstraint(["level_id"], ["levels.id"]),
        sa.ForeignKeyConstraint(["mentor_id"], ["teacher_profiles.id"]),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )


def downgrade() -> None:
    op.drop_table("classes")
    op.drop_table("levels")
    op.drop_table("tracks")
    op.drop_table("cycles")
    op.drop_table("branches")
