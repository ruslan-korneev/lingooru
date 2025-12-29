"""SRS repositories for Review and ReviewLog."""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.types.repositories import BaseRepository
from src.modules.srs.dto import (
    ReviewCreateDTO,
    ReviewLogCreateDTO,
    ReviewLogReadDTO,
    ReviewReadDTO,
    ReviewWithWordDTO,
)
from src.modules.srs.models import Review, ReviewLog
from src.modules.vocabulary.models import Language, Translation, UserWord, Word


class ReviewRepository(BaseRepository[Review, ReviewCreateDTO, ReviewReadDTO]):
    _model = Review
    _create_dto = ReviewCreateDTO
    _read_dto = ReviewReadDTO

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_id(self, review_id: UUID) -> ReviewReadDTO | None:
        """Get review by ID."""
        query = select(self._model).where(self._model.id == review_id)
        result = await self._session.execute(query)
        instance = result.scalar_one_or_none()
        return self._read_dto.model_validate(instance) if instance else None

    async def get_by_user_word_id(self, user_word_id: UUID) -> ReviewReadDTO | None:
        """Get review by user_word_id."""
        query = select(self._model).where(self._model.user_word_id == user_word_id)
        result = await self._session.execute(query)
        instance = result.scalar_one_or_none()
        return self._read_dto.model_validate(instance) if instance else None

    async def get_due_reviews_for_user(
        self,
        user_id: UUID,
        target_language: Language,
        limit: int = 20,
    ) -> Sequence[ReviewWithWordDTO]:
        """Get reviews due for user with word details."""
        now = datetime.now(tz=UTC)
        query = (
            select(
                self._model.id,
                self._model.user_word_id,
                Word.id.label("word_id"),
                Word.text.label("word_text"),
                Word.phonetic.label("word_phonetic"),
                Translation.translated_text.label("translation"),
                Translation.example_sentence,
                self._model.next_review,
            )
            .join(UserWord, self._model.user_word_id == UserWord.id)
            .join(Word, UserWord.word_id == Word.id)
            .join(Translation, Translation.word_id == Word.id)
            .where(
                UserWord.user_id == user_id,
                UserWord.is_learned == True,  # noqa: E712
                Translation.target_language == target_language,
                self._model.next_review <= now,
            )
            .order_by(self._model.next_review)
            .limit(limit)
        )
        result = await self._session.execute(query)
        return [ReviewWithWordDTO.model_validate(row._mapping) for row in result.all()]  # noqa: SLF001

    async def count_due_reviews(self, user_id: UUID) -> int:
        """Count reviews due for user."""
        now = datetime.now(tz=UTC)
        query = (
            select(func.count())
            .select_from(self._model)
            .join(UserWord, self._model.user_word_id == UserWord.id)
            .where(
                UserWord.user_id == user_id,
                UserWord.is_learned == True,  # noqa: E712
                self._model.next_review <= now,
            )
        )
        result = await self._session.execute(query)
        return result.scalar_one()

    async def update_review(
        self,
        review_id: UUID,
        easiness: float,
        interval: int,
        repetitions: int,
        next_review: datetime,
        last_review: datetime,
    ) -> None:
        """Update review SM-2 parameters."""
        query = select(self._model).where(self._model.id == review_id)
        result = await self._session.execute(query)
        review = result.scalar_one_or_none()
        if review:
            review.easiness = easiness
            review.interval = interval
            review.repetitions = repetitions
            review.next_review = next_review
            review.last_review = last_review
            await self._session.flush()


class ReviewLogRepository(BaseRepository[ReviewLog, ReviewLogCreateDTO, ReviewLogReadDTO]):
    _model = ReviewLog
    _create_dto = ReviewLogCreateDTO
    _read_dto = ReviewLogReadDTO

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_average_quality_for_reviews(
        self,
        review_ids: list[UUID],
    ) -> float:
        """Calculate average quality for a set of reviews (most recent log per review)."""
        if not review_ids:
            return 0.0

        # Get the most recent log entry for each review in the list
        subquery = (
            select(
                self._model.review_id,
                func.max(self._model.created_at).label("max_created_at"),
            )
            .where(self._model.review_id.in_(review_ids))
            .group_by(self._model.review_id)
            .subquery()
        )

        query = select(func.avg(self._model.quality)).join(
            subquery,
            (self._model.review_id == subquery.c.review_id) & (self._model.created_at == subquery.c.max_created_at),
        )
        result = await self._session.execute(query)
        avg = result.scalar_one_or_none()
        return float(avg) if avg else 0.0
