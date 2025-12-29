import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import UUID as SA_UUID
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import SAModel


class Language(str, Enum):
    """Supported languages."""

    EN = "en"
    KO = "ko"
    RU = "ru"


class Word(SAModel):
    """Global word dictionary - shared across all users."""

    __tablename__ = "words"

    id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    text: Mapped[str] = mapped_column(String(255), index=True)
    language: Mapped[Language] = mapped_column(index=True)
    phonetic: Mapped[str | None] = mapped_column(String(100), nullable=True)
    audio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    audio_source: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    # Relationships
    translations: Mapped[list["Translation"]] = relationship(
        back_populates="word",
        cascade="all, delete-orphan",
    )
    user_words: Mapped[list["UserWord"]] = relationship(
        back_populates="word",
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint("text", "language", name="words_text_language_key"),)


class Translation(SAModel):
    """Word translations to different languages."""

    __tablename__ = "translations"

    id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    word_id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID,
        ForeignKey("words.id", ondelete="CASCADE"),
        index=True,
    )
    translated_text: Mapped[str] = mapped_column(String(255))
    target_language: Mapped[Language]
    example_sentence: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    # Relationships
    word: Mapped["Word"] = relationship(back_populates="translations")

    __table_args__ = (
        UniqueConstraint(
            "word_id",
            "target_language",
            name="translations_word_target_key",
        ),
    )


class UserWord(SAModel):
    """User's personal vocabulary - links users to words."""

    __tablename__ = "user_words"

    id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    word_id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID,
        ForeignKey("words.id", ondelete="CASCADE"),
        index=True,
    )

    added_at: Mapped[datetime] = mapped_column(default=datetime.now)
    is_learned: Mapped[bool] = mapped_column(default=False)

    # Relationships
    word: Mapped["Word"] = relationship(back_populates="user_words")

    __table_args__ = (UniqueConstraint("user_id", "word_id", name="user_words_user_word_key"),)


class UserWordList(SAModel):
    """Tracks which word lists a user has added."""

    __tablename__ = "user_word_lists"

    id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    word_list_id: Mapped[str] = mapped_column(String(50), index=True)
    added_at: Mapped[datetime] = mapped_column(default=datetime.now)
    words_added: Mapped[int] = mapped_column(default=0)

    __table_args__ = (UniqueConstraint("user_id", "word_list_id", name="user_word_lists_user_list_key"),)
