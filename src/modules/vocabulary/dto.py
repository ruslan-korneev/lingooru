from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.core.types.dto import BaseDTO
from src.modules.vocabulary.models import Language


# Word DTOs
class WordCreateDTO(BaseDTO):
    text: str = Field(min_length=1, max_length=255)
    language: Language
    phonetic: str | None = None
    audio_url: str | None = None


class WordReadDTO(BaseDTO):
    id: UUID
    text: str
    language: Language
    phonetic: str | None
    audio_url: str | None
    created_at: datetime


class WordWithTranslationDTO(BaseDTO):
    """Word with its translation for display."""

    id: UUID
    text: str
    language: Language
    phonetic: str | None
    audio_url: str | None
    translation: str
    example_sentence: str | None


# Translation DTOs
class TranslationCreateDTO(BaseDTO):
    word_id: UUID
    translated_text: str = Field(min_length=1, max_length=255)
    target_language: Language
    example_sentence: str | None = None


class TranslationReadDTO(BaseDTO):
    id: UUID
    word_id: UUID
    translated_text: str
    target_language: Language
    example_sentence: str | None
    created_at: datetime


# UserWord DTOs
class UserWordCreateDTO(BaseDTO):
    user_id: UUID
    word_id: UUID


class UserWordReadDTO(BaseDTO):
    id: UUID
    user_id: UUID
    word_id: UUID
    added_at: datetime
    is_learned: bool


class UserWordWithDetailsDTO(BaseDTO):
    """UserWord with full word and translation details."""

    id: UUID
    user_id: UUID
    word: WordWithTranslationDTO
    added_at: datetime
    is_learned: bool


# Manual word input DTO
class ManualWordInputDTO(BaseDTO):
    """For when API lookup fails and user provides translation."""

    text: str = Field(min_length=1, max_length=255)
    translation: str = Field(min_length=1, max_length=255)
    example_sentence: str | None = None


# UserWordList DTOs
class UserWordListCreateDTO(BaseDTO):
    user_id: UUID
    word_list_id: str = Field(min_length=1, max_length=50)
    words_added: int = 0


class UserWordListReadDTO(BaseDTO):
    id: UUID
    user_id: UUID
    word_list_id: str
    added_at: datetime
    words_added: int
