"""
add_users_table

Revision ID: 3ddedd537f4e
Revises:
Date: 2025-12-29 01:40:48.967760+00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "3ddedd537f4e"
down_revision = None
branch_labels = None
depends_on = None

ui_language_type = sa.Enum("RU", "EN", "KO", name="uilanguage")
language_pair_type = sa.Enum("EN_RU", "KO_RU", name="languagepair")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("ui_language", ui_language_type, nullable=False),
        sa.Column("language_pair", language_pair_type, nullable=False),
        sa.Column("timezone", sa.String(length=50), nullable=False),
        sa.Column("notifications_enabled", sa.Boolean(), nullable=False),
        sa.Column("notification_times", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("users_pkey")),
    )
    op.create_index(op.f("users_telegram_id_idx"), "users", ["telegram_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("users_telegram_id_idx"), table_name="users")
    op.drop_table("users")
    ui_language_type.drop(bind=op.get_bind(), checkfirst=True)
    language_pair_type.drop(bind=op.get_bind(), checkfirst=True)
