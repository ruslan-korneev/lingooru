"""Tests for vocabulary handler."""

from unittest.mock import AsyncMock, MagicMock, patch

from src.bot.handlers.learn import LearnStates
from src.bot.handlers.vocabulary import (
    on_noop,
    on_text_input,
    on_vocab_filter,
    on_vocab_list,
    on_vocab_page,
    show_vocabulary_page,
)
from src.modules.users.dto import UserReadDTO


class TestOnVocabList:
    """Tests for on_vocab_list handler."""

    async def test_resets_filter_and_shows_page(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler resets filter and shows vocabulary page."""
        with patch("src.bot.handlers.vocabulary.show_vocabulary_page", new_callable=AsyncMock) as mock_show:
            await on_vocab_list(mock_callback, mock_i18n, db_user, mock_state)

        mock_state.update_data.assert_called_with(vocab_filter=None)
        mock_show.assert_called_once_with(mock_callback, mock_i18n, db_user, mock_state, page=0)


class TestOnVocabPage:
    """Tests for on_vocab_page handler."""

    async def test_returns_early_when_no_data(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when callback has no data."""
        mock_callback.data = None

        with patch("src.bot.handlers.vocabulary.show_vocabulary_page", new_callable=AsyncMock) as mock_show:
            await on_vocab_page(mock_callback, mock_i18n, db_user, mock_state)

        mock_show.assert_not_called()

    async def test_navigates_to_page(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler navigates to specified page."""
        mock_callback.data = "vocab:page:2"

        with patch("src.bot.handlers.vocabulary.show_vocabulary_page", new_callable=AsyncMock) as mock_show:
            await on_vocab_page(mock_callback, mock_i18n, db_user, mock_state)

        mock_show.assert_called_once()


class TestOnVocabFilter:
    """Tests for on_vocab_filter handler."""

    async def test_returns_early_when_no_data(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when callback has no data."""
        mock_callback.data = None

        await on_vocab_filter(mock_callback, mock_i18n, db_user, mock_state)

        mock_state.update_data.assert_not_called()

    async def test_filters_by_english(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler filters by English language."""
        mock_callback.data = "vocab:filter:en"

        with patch("src.bot.handlers.vocabulary.show_vocabulary_page", new_callable=AsyncMock) as mock_show:
            await on_vocab_filter(mock_callback, mock_i18n, db_user, mock_state)

        mock_state.update_data.assert_called()
        mock_show.assert_called_once()

    async def test_filters_by_korean(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler filters by Korean language."""
        mock_callback.data = "vocab:filter:ko"

        with patch("src.bot.handlers.vocabulary.show_vocabulary_page", new_callable=AsyncMock) as mock_show:
            await on_vocab_filter(mock_callback, mock_i18n, db_user, mock_state)

        mock_state.update_data.assert_called()
        mock_show.assert_called_once()

    async def test_filters_all(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler shows all languages when filter is 'all'."""
        mock_callback.data = "vocab:filter:all"

        with patch("src.bot.handlers.vocabulary.show_vocabulary_page", new_callable=AsyncMock) as mock_show:
            await on_vocab_filter(mock_callback, mock_i18n, db_user, mock_state)

        mock_state.update_data.assert_called_with(vocab_filter=None)
        mock_show.assert_called_once()


class TestShowVocabularyPage:
    """Tests for show_vocabulary_page handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await show_vocabulary_page(mock_callback, mock_i18n, db_user, mock_state, page=0)

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

        await show_vocabulary_page(mock_callback, mock_i18n, db_user, mock_state, page=0)

        mock_callback.answer.assert_not_called()

    async def test_shows_empty_message_when_no_items(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows empty message when no vocabulary items."""
        mock_callback.message = mock_message

        mock_response = MagicMock()
        mock_response.items = []
        mock_response.total = 0

        with patch("src.bot.handlers.vocabulary.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.vocabulary.VocabularyService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_user_vocabulary = AsyncMock(return_value=mock_response)

                await show_vocabulary_page(mock_callback, mock_i18n, db_user, mock_state, page=0)

        mock_i18n.get.assert_any_call("vocab-empty")
        mock_callback.answer.assert_called_once()

    async def test_shows_vocabulary_list(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows vocabulary list with items."""
        mock_callback.message = mock_message

        # Create a mock response that mimics PaginatedResponse
        mock_response = MagicMock()
        mock_response.total = 1

        mock_word = MagicMock()
        mock_word.text = "hello"
        mock_word.translation = "привет"
        mock_word.language = MagicMock()
        mock_word.language.value = "en"

        mock_item = MagicMock()
        mock_item.word = mock_word
        mock_item.is_learned = False

        mock_response.items = [mock_item]

        with patch("src.bot.handlers.vocabulary.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.vocabulary.VocabularyService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_user_vocabulary = AsyncMock(return_value=mock_response)

                await show_vocabulary_page(mock_callback, mock_i18n, db_user, mock_state, page=0)

        mock_message.edit_text.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnTextInput:
    """Tests for on_text_input handler."""

    async def test_skips_when_in_learning_session(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler skips when user is in learning session."""
        mock_state.get_state = AsyncMock(return_value=LearnStates.learning_session.state)
        mock_message.text = "hello"

        await on_text_input(mock_message, mock_i18n, db_user, mock_state)

        mock_message.answer.assert_not_called()

    async def test_skips_when_waiting_for_translation(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler skips when user is waiting for translation."""
        mock_state.get_state = AsyncMock(return_value=LearnStates.waiting_for_translation.state)
        mock_message.text = "hello"

        await on_text_input(mock_message, mock_i18n, db_user, mock_state)

        mock_message.answer.assert_not_called()

    async def test_skips_empty_text(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler skips empty text."""
        mock_state.get_state = AsyncMock(return_value=None)
        mock_message.text = "   "

        await on_text_input(mock_message, mock_i18n, db_user, mock_state)

        mock_message.answer.assert_not_called()

    async def test_skips_long_text(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler skips text longer than MAX_WORD_LENGTH."""
        mock_state.get_state = AsyncMock(return_value=None)
        mock_message.text = "a" * 101

        await on_text_input(mock_message, mock_i18n, db_user, mock_state)

        mock_message.answer.assert_not_called()


class TestOnNoop:
    """Tests for on_noop handler."""

    async def test_answers_callback(
        self,
        mock_callback: MagicMock,
    ) -> None:
        """Handler answers callback."""
        await on_noop(mock_callback)

        mock_callback.answer.assert_called_once()
