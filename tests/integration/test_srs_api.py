"""Integration tests for SRS API endpoints."""

from uuid import uuid4

from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.srs.services import SRSService
from src.modules.users.dto import UserReadDTO
from src.modules.vocabulary.enums import Language
from src.modules.vocabulary.services import VocabularyService


class TestSRSAPI:
    """Integration tests for /v1/reviews endpoints."""

    async def test_count_due_reviews_returns_zero_for_empty_user(
        self,
        api_client: AsyncClient,
        sample_user: UserReadDTO,
    ) -> None:
        """Test counting due reviews for user with no reviews."""
        response = await api_client.get(f"/v1/reviews/count/{sample_user.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == 0

    async def test_count_due_reviews_counts_due_words(
        self,
        api_client: AsyncClient,
        session: AsyncSession,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
        srs_service: SRSService,
    ) -> None:
        """Test counting due reviews with words."""
        # Add and learn words
        for i in range(3):
            user_word = await vocabulary_service.add_word_with_translation(
                user_id=sample_user.id,
                text=f"api_count_word_{i}",
                translation=f"счётчик_{i}",
                source_language=Language.EN,
                target_language=Language.RU,
            )
            await vocabulary_service.mark_word_learned(user_word.id)
            await srs_service.get_or_create_review(user_word.id)
        await session.flush()

        response = await api_client.get(f"/v1/reviews/count/{sample_user.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == 3  # noqa: PLR2004

    async def test_get_due_reviews_returns_empty_list(
        self,
        api_client: AsyncClient,
        sample_user: UserReadDTO,
    ) -> None:
        """Test getting due reviews for user with no reviews."""
        response = await api_client.get(
            f"/v1/reviews/due/{sample_user.id}",
            params={"target_language": "ru"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_get_due_reviews_returns_word_details(
        self,
        api_client: AsyncClient,
        session: AsyncSession,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
        srs_service: SRSService,
    ) -> None:
        """Test that due reviews include word details."""
        user_word = await vocabulary_service.add_word_with_translation(
            user_id=sample_user.id,
            text="api_details_word",
            translation="апи детали",
            source_language=Language.EN,
            target_language=Language.RU,
            phonetic="/ˈdɪːteɪlz/",  # noqa: RUF001
        )
        await vocabulary_service.mark_word_learned(user_word.id)
        await srs_service.get_or_create_review(user_word.id)
        await session.flush()

        response = await api_client.get(
            f"/v1/reviews/due/{sample_user.id}",
            params={"target_language": "ru"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        review = data["items"][0]
        assert review["word_text"] == "api_details_word"
        assert review["translation"] == "апи детали"
        assert review["word_phonetic"] == "/ˈdɪːteɪlz/"  # noqa: RUF001

    async def test_get_review_by_id(
        self,
        api_client: AsyncClient,
        session: AsyncSession,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
        srs_service: SRSService,
    ) -> None:
        """Test getting review by ID."""
        user_word = await vocabulary_service.add_word_with_translation(
            user_id=sample_user.id,
            text="api_get_by_id",
            translation="получить по ид",
            source_language=Language.EN,
            target_language=Language.RU,
        )
        await vocabulary_service.mark_word_learned(user_word.id)
        review = await srs_service.get_or_create_review(user_word.id)
        await session.flush()

        response = await api_client.get(f"/v1/reviews/{review.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(review.id)
        assert data["user_word_id"] == str(user_word.id)
        assert data["easiness"] == 2.5  # noqa: PLR2004
        assert data["repetitions"] == 0

    async def test_get_review_not_found(
        self,
        api_client: AsyncClient,
    ) -> None:
        """Test getting non-existent review."""
        response = await api_client.get(f"/v1/reviews/{uuid4()}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_rate_review_updates_sm2_params(
        self,
        api_client: AsyncClient,
        session: AsyncSession,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
        srs_service: SRSService,
    ) -> None:
        """Test that rating a review updates SM-2 parameters."""
        user_word = await vocabulary_service.add_word_with_translation(
            user_id=sample_user.id,
            text="api_rate_word",
            translation="оценить слово",
            source_language=Language.EN,
            target_language=Language.RU,
        )
        await vocabulary_service.mark_word_learned(user_word.id)
        review = await srs_service.get_or_create_review(user_word.id)
        await session.flush()

        response = await api_client.post(
            f"/v1/reviews/{review.id}/rate",
            json={"quality": 5},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["repetitions"] == 1
        assert data["interval"] == 1
        assert data["last_review"] is not None

    async def test_rate_review_with_failure_resets(
        self,
        api_client: AsyncClient,
        session: AsyncSession,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
        srs_service: SRSService,
    ) -> None:
        """Test that failed rating resets SM-2 parameters."""
        user_word = await vocabulary_service.add_word_with_translation(
            user_id=sample_user.id,
            text="api_fail_word",
            translation="неудачное слово",
            source_language=Language.EN,
            target_language=Language.RU,
        )
        await vocabulary_service.mark_word_learned(user_word.id)
        review = await srs_service.get_or_create_review(user_word.id)
        await session.flush()

        # First successful rating
        await api_client.post(
            f"/v1/reviews/{review.id}/rate",
            json={"quality": 4},
        )

        # Failed rating
        response = await api_client.post(
            f"/v1/reviews/{review.id}/rate",
            json={"quality": 1},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["repetitions"] == 0
        assert data["interval"] == 1

    async def test_rate_review_not_found(
        self,
        api_client: AsyncClient,
    ) -> None:
        """Test rating non-existent review."""
        response = await api_client.post(
            f"/v1/reviews/{uuid4()}/rate",
            json={"quality": 5},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_rate_review_invalid_quality(
        self,
        api_client: AsyncClient,
        session: AsyncSession,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
        srs_service: SRSService,
    ) -> None:
        """Test that invalid quality is rejected."""
        user_word = await vocabulary_service.add_word_with_translation(
            user_id=sample_user.id,
            text="api_invalid_quality",
            translation="неверное качество",
            source_language=Language.EN,
            target_language=Language.RU,
        )
        await vocabulary_service.mark_word_learned(user_word.id)
        review = await srs_service.get_or_create_review(user_word.id)
        await session.flush()

        # Quality 0 (below minimum)
        response = await api_client.post(
            f"/v1/reviews/{review.id}/rate",
            json={"quality": 0},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Quality 6 (above maximum)
        response = await api_client.post(
            f"/v1/reviews/{review.id}/rate",
            json={"quality": 6},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
