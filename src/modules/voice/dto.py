"""Voice module Data Transfer Objects."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.core.types.dto import BaseDTO


class PronunciationFeedback(BaseDTO):
    """Result from GPT-4o pronunciation check."""

    rating: int = Field(ge=1, le=5)
    feedback: str
    is_correct: bool


class PronunciationLogCreateDTO(BaseDTO):
    """DTO for creating pronunciation log."""

    user_id: UUID
    word_id: UUID
    transcribed_text: str
    expected_text: str
    rating: int = Field(ge=1, le=5)
    feedback: str
    audio_duration_seconds: float | None = None


class PronunciationLogReadDTO(BaseDTO):
    """DTO for reading pronunciation log."""

    id: UUID
    user_id: UUID
    word_id: UUID
    transcribed_text: str
    expected_text: str
    rating: int
    feedback: str
    audio_duration_seconds: float | None
    created_at: datetime


class WordForPronunciationDTO(BaseDTO):
    """Word with details for pronunciation practice."""

    id: UUID
    user_word_id: UUID
    text: str
    phonetic: str | None
    audio_url: str | None
    language: str


class PronunciationSessionStatsDTO(BaseDTO):
    """Statistics for completed pronunciation session."""

    total_practiced: int
    average_rating: float
    time_spent_seconds: int
