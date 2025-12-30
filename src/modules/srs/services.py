"""SRS service - business logic for spaced repetition."""

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.srs.algorithm import calculate_sm2
from src.modules.srs.dto import (
    ReviewCreateDTO,
    ReviewLogCreateDTO,
    ReviewReadDTO,
    ReviewSessionStatsDTO,
    ReviewWithWordDTO,
)
from src.modules.srs.repositories import ReviewLogRepository, ReviewRepository
from src.modules.vocabulary.enums import Language


class SRSService:
    """Service for managing spaced repetition reviews."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._review_repo = ReviewRepository(session)
        self._log_repo = ReviewLogRepository(session)

    async def get_or_create_review(self, user_word_id: UUID) -> ReviewReadDTO:
        """Get existing review or create new one for user_word."""
        existing = await self._review_repo.get_by_user_word_id(user_word_id)
        if existing:
            return existing

        dto = ReviewCreateDTO(user_word_id=user_word_id)
        return await self._review_repo.save(dto)

    async def get_review_by_id(self, review_id: UUID) -> ReviewReadDTO | None:
        """Get review by ID."""
        return await self._review_repo.get_by_id(review_id)

    async def get_due_reviews(
        self,
        user_id: UUID,
        target_language: Language,
        limit: int = 20,
    ) -> Sequence[ReviewWithWordDTO]:
        """Get reviews that are due for the user."""
        return await self._review_repo.get_due_reviews_for_user(
            user_id=user_id,
            target_language=target_language,
            limit=limit,
        )

    async def count_due_reviews(self, user_id: UUID) -> int:
        """Count how many reviews are due."""
        return await self._review_repo.count_due_reviews(user_id)

    async def record_review(
        self,
        review_id: UUID,
        quality: int,
        response_time_ms: int | None = None,
    ) -> None:
        """
        Record a review response and update SM-2 parameters.

        Args:
            review_id: The review to update
            quality: Rating 1-5
            response_time_ms: Time taken to respond in milliseconds
        """
        # Get current review state
        review = await self._review_repo.get_by_id(review_id)
        if not review:
            return

        # Calculate new SM-2 values
        result = calculate_sm2(
            quality=quality,
            repetitions=review.repetitions,
            easiness=review.easiness,
            interval=review.interval,
        )

        # Calculate next review date
        now = datetime.now(tz=UTC)
        next_review = now + timedelta(days=result.interval)

        # Update review
        await self._review_repo.update_review(
            review_id=review_id,
            easiness=result.easiness,
            interval=result.interval,
            repetitions=result.repetitions,
            next_review=next_review,
            last_review=now,
        )

        # Log the response
        log_dto = ReviewLogCreateDTO(
            review_id=review_id,
            quality=quality,
            response_time_ms=response_time_ms,
        )
        await self._log_repo.save(log_dto)

    async def get_session_stats(
        self,
        review_ids: list[UUID],
        session_start: datetime,
    ) -> ReviewSessionStatsDTO:
        """Get statistics for a completed review session."""
        avg_quality = await self._log_repo.get_average_quality_for_reviews(review_ids)
        time_spent = int((datetime.now(tz=UTC) - session_start).total_seconds())

        return ReviewSessionStatsDTO(
            total_reviewed=len(review_ids),
            average_quality=round(avg_quality, 1),
            time_spent_seconds=time_spent,
        )
