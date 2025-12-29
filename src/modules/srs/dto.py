"""SRS Data Transfer Objects."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.core.types.dto import BaseDTO


class ReviewCreateDTO(BaseDTO):
    """DTO for creating a new review."""

    user_word_id: UUID


class ReviewReadDTO(BaseDTO):
    """DTO for reading review data."""

    id: UUID
    user_word_id: UUID
    easiness: float
    interval: int
    repetitions: int
    next_review: datetime
    last_review: datetime | None
    created_at: datetime


class ReviewUpdateDTO(BaseDTO):
    """DTO for updating review after rating."""

    easiness: float
    interval: int
    repetitions: int
    next_review: datetime
    last_review: datetime


class ReviewLogCreateDTO(BaseDTO):
    """DTO for creating a review log entry."""

    review_id: UUID
    quality: int = Field(ge=1, le=5)
    response_time_ms: int | None = None


class ReviewLogReadDTO(BaseDTO):
    """DTO for reading review log data."""

    id: UUID
    review_id: UUID
    quality: int
    response_time_ms: int | None
    created_at: datetime


class ReviewWithWordDTO(BaseDTO):
    """Review with word details for display in bot."""

    id: UUID
    user_word_id: UUID
    word_id: UUID
    word_text: str
    word_phonetic: str | None
    translation: str
    example_sentence: str | None
    next_review: datetime


class ReviewSessionStatsDTO(BaseDTO):
    """Statistics for completed review session."""

    total_reviewed: int
    average_quality: float
    time_spent_seconds: int


class ReviewRateRequestDTO(BaseDTO):
    """Request DTO for rating a review."""

    quality: int = Field(ge=1, le=5)
    response_time_ms: int | None = None


class DueReviewsCountDTO(BaseDTO):
    """DTO for due reviews count response."""

    count: int
