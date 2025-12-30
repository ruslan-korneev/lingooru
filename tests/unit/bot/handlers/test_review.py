"""Tests for review handler."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.bot.handlers.review import (
    ReviewStates,
    on_review_begin,
    on_review_rate,
    on_review_show_answer,
    on_review_start,
)
from src.modules.srs.dto import ReviewWithWordDTO
from src.modules.users.dto import UserReadDTO


class TestOnReviewStart:
    """Tests for on_review_start handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await on_review_start(mock_callback, mock_i18n, db_user, mock_state)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.message = MagicMock()  # Not a Message instance

        await on_review_start(mock_callback, mock_i18n, db_user, mock_state)

        # Should return early, no state clear
        mock_state.clear.assert_not_called()

    async def test_shows_no_words_due_when_count_zero(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Shows 'no words due' message when count is 0."""
        mock_callback.message = mock_message

        with patch("src.bot.handlers.review.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.review.SRSService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.count_due_reviews = AsyncMock(return_value=0)

                await on_review_start(mock_callback, mock_i18n, db_user, mock_state)

        mock_callback.answer.assert_called_once()
        mock_i18n.get.assert_any_call("review-no-words-due")

    async def test_shows_due_count_when_words_available(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Shows start screen with due count when words are available."""
        mock_callback.message = mock_message

        with patch("src.bot.handlers.review.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.review.SRSService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.count_due_reviews = AsyncMock(return_value=5)

                await on_review_start(mock_callback, mock_i18n, db_user, mock_state)

        mock_callback.answer.assert_called_once()
        mock_i18n.get.assert_any_call("review-start", count=5)


class TestOnReviewBegin:
    """Tests for on_review_begin handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await on_review_begin(mock_callback, mock_i18n, db_user, mock_state)

        mock_callback.answer.assert_not_called()

    async def test_shows_no_words_when_reviews_empty(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Shows 'no words' when reviews list is empty."""
        mock_callback.message = mock_message

        with patch("src.bot.handlers.review.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.review.SRSService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_due_reviews = AsyncMock(return_value=[])

                await on_review_begin(mock_callback, mock_i18n, db_user, mock_state)

        mock_i18n.get.assert_any_call("review-no-words-due")

    async def test_begins_session_with_reviews(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Begins review session and shows first question."""
        mock_callback.message = mock_message

        review = ReviewWithWordDTO(
            id=uuid4(),
            user_word_id=uuid4(),
            word_id=uuid4(),
            word_text="hello",
            word_phonetic="/helo/",
            translation="привет",
            example_sentence="Hello world",
            next_review=datetime.now(tz=UTC),
        )

        with patch("src.bot.handlers.review.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.review.SRSService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_due_reviews = AsyncMock(return_value=[review])

                await on_review_begin(mock_callback, mock_i18n, db_user, mock_state)

        mock_state.update_data.assert_called_once()
        mock_state.set_state.assert_called_with(ReviewStates.reviewing)


class TestOnReviewShowAnswer:
    """Tests for on_review_show_answer handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await on_review_show_answer(mock_callback, mock_i18n, mock_state)

        mock_state.get_data.assert_not_called()

    async def test_clears_state_when_no_reviews(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Clears state when no reviews in data."""
        mock_callback.message = mock_message
        mock_state.get_data = AsyncMock(return_value={"reviews": []})

        await on_review_show_answer(mock_callback, mock_i18n, mock_state)

        mock_state.clear.assert_called_once()

    async def test_shows_answer_with_phonetic(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Shows answer with phonetic when available."""
        mock_callback.message = mock_message
        review_data = {
            "id": str(uuid4()),
            "word_id": str(uuid4()),
            "word_text": "hello",
            "word_phonetic": "/helo/",
            "translation": "привет",
            "example_sentence": "Hello world",
        }
        mock_state.get_data = AsyncMock(return_value={"reviews": [review_data], "current_index": 0})

        await on_review_show_answer(mock_callback, mock_i18n, mock_state)

        mock_state.set_state.assert_called_with(ReviewStates.rating)
        mock_callback.answer.assert_called_once()


class TestOnReviewRate:
    """Tests for on_review_rate handler."""

    async def test_returns_early_when_no_data_or_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when callback has no data or message."""
        mock_callback.data = None
        mock_callback.message = MagicMock()

        await on_review_rate(mock_callback, mock_i18n, mock_state)

        mock_state.get_data.assert_not_called()

    async def test_clears_state_when_no_reviews(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Clears state when no reviews in data."""
        mock_callback.message = mock_message
        mock_callback.data = "review:rate:5"
        mock_state.get_data = AsyncMock(return_value={"reviews": []})

        await on_review_rate(mock_callback, mock_i18n, mock_state)

        mock_state.clear.assert_called_once()

    async def test_records_review_and_moves_to_next(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Records review and moves to next word."""
        mock_callback.message = mock_message
        mock_callback.data = "review:rate:4"

        review_data = [
            {"id": str(uuid4()), "translation": "привет"},
            {"id": str(uuid4()), "translation": "мир"},
        ]
        mock_state.get_data = AsyncMock(
            return_value={
                "reviews": review_data,
                "current_index": 0,
                "reviewed_ids": [],
                "session_start": datetime.now(tz=UTC).isoformat(),
            }
        )

        with patch("src.bot.handlers.review.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.review.SRSService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.record_review = AsyncMock()

                await on_review_rate(mock_callback, mock_i18n, mock_state)

        mock_state.update_data.assert_called()
        mock_state.set_state.assert_called_with(ReviewStates.reviewing)

    async def test_completes_session_on_last_word(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Completes session and shows stats on last word."""
        mock_callback.message = mock_message
        mock_callback.data = "review:rate:5"

        review_data = [{"id": str(uuid4()), "translation": "привет"}]
        mock_state.get_data = AsyncMock(
            return_value={
                "reviews": review_data,
                "current_index": 0,
                "reviewed_ids": [],
                "session_start": datetime.now(tz=UTC).isoformat(),
            }
        )

        with patch("src.bot.handlers.review.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.review.SRSService") as mock_service_class:
                from src.modules.srs.dto import ReviewSessionStatsDTO

                mock_service = mock_service_class.return_value
                mock_service.record_review = AsyncMock()
                mock_service.get_session_stats = AsyncMock(
                    return_value=ReviewSessionStatsDTO(
                        total_reviewed=1,
                        average_quality=5.0,
                        time_spent_seconds=60,
                    )
                )

                await on_review_rate(mock_callback, mock_i18n, mock_state)

        mock_state.clear.assert_called_once()
        mock_i18n.get.assert_any_call("review-session-ended")
