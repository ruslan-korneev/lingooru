"""Unit tests for SRS service."""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.srs.services import SRSService
from src.modules.users.dto import UserReadDTO
from src.modules.vocabulary.enums import Language
from src.modules.vocabulary.services import VocabularyService


class TestSRSService:
    """Test cases for SRS service."""

    async def test_get_or_create_review_creates_new(
        self,
        session: AsyncSession,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
        srs_service: SRSService,
    ) -> None:
        """Test that get_or_create_review creates a new review."""
        # Add and learn a word
        user_word = await vocabulary_service.add_word_with_translation(
            user_id=sample_user.id,
            text="srs_test_create",
            translation="тест создания",
            source_language=Language.EN,
            target_language=Language.RU,
        )
        await vocabulary_service.mark_word_learned(user_word.id)
        await session.flush()

        # Create review
        review = await srs_service.get_or_create_review(user_word.id)

        assert review is not None
        assert review.user_word_id == user_word.id
        assert review.easiness == 2.5  # noqa: PLR2004
        assert review.repetitions == 0
        assert review.interval == 0

    async def test_get_or_create_review_returns_existing(
        self,
        session: AsyncSession,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
        srs_service: SRSService,
    ) -> None:
        """Test that get_or_create_review returns existing review."""
        user_word = await vocabulary_service.add_word_with_translation(
            user_id=sample_user.id,
            text="srs_test_existing",
            translation="существующий",
            source_language=Language.EN,
            target_language=Language.RU,
        )
        await vocabulary_service.mark_word_learned(user_word.id)
        await session.flush()

        # Create first review
        review1 = await srs_service.get_or_create_review(user_word.id)
        # Get same review again
        review2 = await srs_service.get_or_create_review(user_word.id)

        assert review1.id == review2.id

    async def test_count_due_reviews_returns_zero_for_new_user(
        self,
        sample_user: UserReadDTO,
        srs_service: SRSService,
    ) -> None:
        """Test that count_due_reviews returns 0 for user with no reviews."""
        count = await srs_service.count_due_reviews(sample_user.id)

        assert count == 0

    async def test_count_due_reviews_counts_due_words(
        self,
        session: AsyncSession,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
        srs_service: SRSService,
    ) -> None:
        """Test that count_due_reviews counts words due for review."""
        # Add and learn words
        for i in range(3):
            user_word = await vocabulary_service.add_word_with_translation(
                user_id=sample_user.id,
                text=f"due_word_{i}",
                translation=f"слово_{i}",
                source_language=Language.EN,
                target_language=Language.RU,
            )
            await vocabulary_service.mark_word_learned(user_word.id)
            await srs_service.get_or_create_review(user_word.id)
        await session.flush()

        count = await srs_service.count_due_reviews(sample_user.id)

        # All 3 words should be due (next_review defaults to now)
        assert count == 3  # noqa: PLR2004

    async def test_record_review_updates_sm2_params(
        self,
        session: AsyncSession,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
        srs_service: SRSService,
    ) -> None:
        """Test that record_review updates SM-2 parameters."""
        user_word = await vocabulary_service.add_word_with_translation(
            user_id=sample_user.id,
            text="srs_update_test",
            translation="обновление",
            source_language=Language.EN,
            target_language=Language.RU,
        )
        await vocabulary_service.mark_word_learned(user_word.id)
        review = await srs_service.get_or_create_review(user_word.id)
        await session.flush()

        # Record a successful review (quality 5)
        await srs_service.record_review(review.id, quality=5)
        await session.flush()

        # Check updated review
        updated = await srs_service.get_review_by_id(review.id)
        assert updated is not None
        assert updated.repetitions == 1
        assert updated.interval == 1
        assert updated.last_review is not None

    async def test_record_review_resets_on_failure(
        self,
        session: AsyncSession,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
        srs_service: SRSService,
    ) -> None:
        """Test that record_review resets progress on failure."""
        user_word = await vocabulary_service.add_word_with_translation(
            user_id=sample_user.id,
            text="srs_reset_test",
            translation="сброс",  # noqa: RUF001
            source_language=Language.EN,
            target_language=Language.RU,
        )
        await vocabulary_service.mark_word_learned(user_word.id)
        review = await srs_service.get_or_create_review(user_word.id)
        await session.flush()

        # First successful review
        await srs_service.record_review(review.id, quality=4)
        await session.flush()

        # Failed review (quality 1)
        await srs_service.record_review(review.id, quality=1)
        await session.flush()

        # Check that repetitions were reset
        updated = await srs_service.get_review_by_id(review.id)
        assert updated is not None
        assert updated.repetitions == 0
        assert updated.interval == 1

    async def test_get_due_reviews_returns_word_details(
        self,
        session: AsyncSession,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
        srs_service: SRSService,
    ) -> None:
        """Test that get_due_reviews returns word details."""
        user_word = await vocabulary_service.add_word_with_translation(
            user_id=sample_user.id,
            text="details_test",
            translation="детали",
            source_language=Language.EN,
            target_language=Language.RU,
            phonetic="/dɪˈteɪlz/",  # noqa: RUF001
        )
        await vocabulary_service.mark_word_learned(user_word.id)
        await srs_service.get_or_create_review(user_word.id)
        await session.flush()

        reviews = await srs_service.get_due_reviews(
            user_id=sample_user.id,
            target_language=Language.RU,
        )

        assert len(reviews) == 1
        review = reviews[0]
        assert review.word_text == "details_test"
        assert review.translation == "детали"
        assert review.word_phonetic == "/dɪˈteɪlz/"  # noqa: RUF001

    async def test_get_session_stats_calculates_correctly(
        self,
        session: AsyncSession,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
        srs_service: SRSService,
    ) -> None:
        """Test that get_session_stats calculates statistics correctly."""
        # Create words and reviews
        review_ids = []
        for i in range(3):
            user_word = await vocabulary_service.add_word_with_translation(
                user_id=sample_user.id,
                text=f"stats_word_{i}",
                translation=f"статистика_{i}",
                source_language=Language.EN,
                target_language=Language.RU,
            )
            await vocabulary_service.mark_word_learned(user_word.id)
            review = await srs_service.get_or_create_review(user_word.id)
            review_ids.append(review.id)
        await session.flush()

        # Record reviews with different qualities
        session_start = datetime.now(tz=UTC)
        await srs_service.record_review(review_ids[0], quality=5)
        await srs_service.record_review(review_ids[1], quality=4)
        await srs_service.record_review(review_ids[2], quality=3)
        await session.flush()

        # Get stats
        stats = await srs_service.get_session_stats(review_ids, session_start)

        assert stats.total_reviewed == 3  # noqa: PLR2004
        assert stats.average_quality == 4.0  # noqa: PLR2004 - (5+4+3)/3 = 4
        assert stats.time_spent_seconds >= 0
