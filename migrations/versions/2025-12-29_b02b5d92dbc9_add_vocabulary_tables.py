"""
add_vocabulary_tables

Revision ID: b02b5d92dbc9
Revises: 3ddedd537f4e
Date: 2025-12-29 02:17:57.431350+00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "b02b5d92dbc9"
down_revision = "3ddedd537f4e"
branch_labels = None
depends_on = None

language_type = sa.Enum("EN", "KO", "RU", name="language")


def upgrade() -> None:
    op.create_table(
        "words",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("text", sa.String(length=255), nullable=False),
        sa.Column("language", language_type, nullable=False),
        sa.Column("phonetic", sa.String(length=100), nullable=True),
        sa.Column("audio_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("words_pkey")),
        sa.UniqueConstraint("text", "language", name="words_text_language_key"),
    )
    op.create_index(op.f("words_language_idx"), "words", ["language"], unique=False)
    op.create_index(op.f("words_text_idx"), "words", ["text"], unique=False)
    op.create_table(
        "translations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("word_id", sa.UUID(), nullable=False),
        sa.Column("translated_text", sa.String(length=255), nullable=False),
        sa.Column("target_language", language_type, nullable=False),
        sa.Column("example_sentence", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["word_id"], ["words.id"], name=op.f("translations_word_id_fkey"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("translations_pkey")),
        sa.UniqueConstraint("word_id", "target_language", name="translations_word_target_key"),
    )
    op.create_index(op.f("translations_word_id_idx"), "translations", ["word_id"], unique=False)
    op.create_table(
        "user_words",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("word_id", sa.UUID(), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_learned", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("user_words_user_id_fkey"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["word_id"], ["words.id"], name=op.f("user_words_word_id_fkey"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("user_words_pkey")),
        sa.UniqueConstraint("user_id", "word_id", name="user_words_user_word_key"),
    )
    op.create_index(op.f("user_words_user_id_idx"), "user_words", ["user_id"], unique=False)
    op.create_index(op.f("user_words_word_id_idx"), "user_words", ["word_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("user_words_word_id_idx"), table_name="user_words")
    op.drop_index(op.f("user_words_user_id_idx"), table_name="user_words")
    op.drop_table("user_words")
    op.drop_index(op.f("translations_word_id_idx"), table_name="translations")
    op.drop_table("translations")
    op.drop_index(op.f("words_text_idx"), table_name="words")
    op.drop_index(op.f("words_language_idx"), table_name="words")
    op.drop_table("words")
    language_type.drop(bind=op.get_bind(), checkfirst=True)
