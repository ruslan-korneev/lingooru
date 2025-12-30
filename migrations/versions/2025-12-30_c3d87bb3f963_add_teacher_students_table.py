"""
add_teacher_students_table

Revision ID: c3d87bb3f963
Revises: 9c0f34667ceb
Date: 2025-12-30 04:26:20.591364+00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "c3d87bb3f963"
down_revision = "9c0f34667ceb"
branch_labels = None
depends_on = None

teacherstudentstatus_type = sa.Enum("PENDING", "ACTIVE", "ARCHIVED", name="teacherstudentstatus")


def upgrade() -> None:
    op.create_table(
        "teacher_students",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("teacher_id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=True),
        sa.Column("invite_code", sa.String(length=12), nullable=False),
        sa.Column(
            "status",
            teacherstudentstatus_type,
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["users.id"],
            name=op.f("teacher_students_student_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["teacher_id"],
            ["users.id"],
            name=op.f("teacher_students_teacher_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("teacher_students_pkey")),
        sa.UniqueConstraint("teacher_id", "student_id", name="teacher_students_teacher_student_key"),
    )
    op.create_index(op.f("teacher_students_invite_code_idx"), "teacher_students", ["invite_code"], unique=True)
    op.create_index(op.f("teacher_students_student_id_idx"), "teacher_students", ["student_id"], unique=False)
    op.create_index(op.f("teacher_students_teacher_id_idx"), "teacher_students", ["teacher_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("teacher_students_teacher_id_idx"), table_name="teacher_students")
    op.drop_index(op.f("teacher_students_student_id_idx"), table_name="teacher_students")
    op.drop_index(op.f("teacher_students_invite_code_idx"), table_name="teacher_students")
    op.drop_table("teacher_students")
    teacherstudentstatus_type.drop(op.get_bind())
