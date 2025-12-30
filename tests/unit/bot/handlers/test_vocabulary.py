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


class TestShowVocabularyPageFilters:
    """Tests for show_vocabulary_page with filter handling."""

    async def test_gets_filter_from_state_when_not_provided(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler gets filter from state when source_filter is None."""
        mock_callback.message = mock_message
        # State contains a filter value
        mock_state.get_data = AsyncMock(return_value={"vocab_filter": "en"})

        mock_response = MagicMock()
        mock_response.items = []
        mock_response.total = 0

        with patch("src.bot.handlers.vocabulary.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.vocabulary.VocabularyService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_user_vocabulary = AsyncMock(return_value=mock_response)

                # Call without source_filter - should read from state
                await show_vocabulary_page(mock_callback, mock_i18n, db_user, mock_state, page=0)

                # Verify get_data was called to retrieve filter
                mock_state.get_data.assert_called_once()
                # Verify vocabulary service was called (with filter from state)
                mock_service.get_user_vocabulary.assert_called_once()

    async def test_skips_state_filter_when_source_filter_provided(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler skips reading state when source_filter is explicitly provided."""
        from src.modules.vocabulary.models import Language

        mock_callback.message = mock_message
        # State contains a different filter value - but should be ignored
        mock_state.get_data = AsyncMock(return_value={"vocab_filter": "en"})

        mock_response = MagicMock()
        mock_response.items = []
        mock_response.total = 0

        with patch("src.bot.handlers.vocabulary.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.vocabulary.VocabularyService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_user_vocabulary = AsyncMock(return_value=mock_response)

                # Call with explicit source_filter - should not read from state
                await show_vocabulary_page(
                    mock_callback, mock_i18n, db_user, mock_state, page=0, source_filter=Language.KO
                )

                # Verify get_data was NOT called since we provided source_filter
                mock_state.get_data.assert_not_called()

    async def test_handles_empty_filter_value_in_state(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler handles empty filter value in state (falsy value)."""
        mock_callback.message = mock_message
        # State has no filter value (empty/None)
        mock_state.get_data = AsyncMock(return_value={"vocab_filter": None})

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

                mock_state.get_data.assert_called_once()
                mock_service.get_user_vocabulary.assert_called_once()


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

    async def test_skips_when_text_is_none(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler skips when message.text is None."""
        mock_state.get_state = AsyncMock(return_value=None)
        mock_message.text = None

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

    async def test_skips_menu_button_text(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler skips menu button text."""
        mock_state.get_state = AsyncMock(return_value=None)
        mock_message.text = "📋 Меню"  # Menu button

        await on_text_input(mock_message, mock_i18n, db_user, mock_state)

        mock_message.answer.assert_not_called()

    async def test_skips_learn_button_text(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler skips learn button text."""
        mock_state.get_state = AsyncMock(return_value=None)
        mock_message.text = "📚 Learn"  # Learn button

        await on_text_input(mock_message, mock_i18n, db_user, mock_state)

        mock_message.answer.assert_not_called()

    async def test_skips_review_button_text(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler skips review button text."""
        mock_state.get_state = AsyncMock(return_value=None)
        mock_message.text = "🔄 Повторять"  # Review button

        await on_text_input(mock_message, mock_i18n, db_user, mock_state)

        mock_message.answer.assert_not_called()

    async def test_adds_word_when_found_in_dictionary(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler adds word to vocabulary when found in dictionary."""
        mock_state.get_state = AsyncMock(return_value=None)
        mock_message.text = "hello"

        # Mock lookup result
        mock_result = MagicMock()
        mock_result.text = "hello"
        mock_result.translation = "привет"
        mock_result.example_sentence = "Hello, world!"
        mock_result.phonetic = "/həˈloʊ/"  # noqa: RUF001
        mock_result.audio_url = "https://example.com/hello.mp3"

        # Mock user word after adding
        mock_word = MagicMock()
        mock_word.text = "hello"
        mock_word.translation = "привет"
        mock_word.phonetic = "/həˈloʊ/"  # noqa: RUF001

        mock_user_word = MagicMock()
        mock_user_word.word = mock_word

        with patch("src.bot.handlers.vocabulary.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.vocabulary.VocabularyService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.lookup_word = AsyncMock(return_value=mock_result)
                mock_service.add_word_with_translation = AsyncMock(return_value=mock_user_word)

                await on_text_input(mock_message, mock_i18n, db_user, mock_state)

        mock_service.lookup_word.assert_called_once()
        mock_service.add_word_with_translation.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_message.answer.assert_called_once()
        mock_i18n.get.assert_any_call("word-added", word="hello", phonetic="\n/həˈloʊ/", translation="привет")  # noqa: RUF001

    async def test_adds_word_without_phonetic(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler adds word without phonetic transcription."""
        mock_state.get_state = AsyncMock(return_value=None)
        mock_message.text = "test"

        mock_result = MagicMock()
        mock_result.text = "test"
        mock_result.translation = "тест"
        mock_result.example_sentence = None
        mock_result.phonetic = None
        mock_result.audio_url = None

        mock_word = MagicMock()
        mock_word.text = "test"
        mock_word.translation = "тест"
        mock_word.phonetic = None  # No phonetic

        mock_user_word = MagicMock()
        mock_user_word.word = mock_word

        with patch("src.bot.handlers.vocabulary.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.vocabulary.VocabularyService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.lookup_word = AsyncMock(return_value=mock_result)
                mock_service.add_word_with_translation = AsyncMock(return_value=mock_user_word)

                await on_text_input(mock_message, mock_i18n, db_user, mock_state)

        # Phonetic should be empty string when None
        mock_i18n.get.assert_any_call("word-added", word="test", phonetic="", translation="тест")

    async def test_handles_word_already_exists_conflict(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler handles ConflictError when word already exists."""
        from src.core.exceptions import ConflictError

        mock_state.get_state = AsyncMock(return_value=None)
        mock_message.text = "hello"

        mock_result = MagicMock()
        mock_result.text = "hello"
        mock_result.translation = "привет"
        mock_result.example_sentence = None
        mock_result.phonetic = None
        mock_result.audio_url = None

        with patch("src.bot.handlers.vocabulary.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.vocabulary.VocabularyService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.lookup_word = AsyncMock(return_value=mock_result)
                mock_service.add_word_with_translation = AsyncMock(side_effect=ConflictError("Word exists"))

                await on_text_input(mock_message, mock_i18n, db_user, mock_state)

        mock_message.answer.assert_called_once()
        mock_i18n.get.assert_any_call("word-already-exists")

    async def test_asks_for_translation_when_word_not_found(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler asks for translation when word not found in dictionary."""
        mock_state.get_state = AsyncMock(return_value=None)
        mock_message.text = "unknownword"

        with patch("src.bot.handlers.vocabulary.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.vocabulary.VocabularyService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.lookup_word = AsyncMock(return_value=None)  # Word not found

                await on_text_input(mock_message, mock_i18n, db_user, mock_state)

        mock_state.update_data.assert_called_with(pending_word="unknownword")
        mock_state.set_state.assert_called_once_with(LearnStates.waiting_for_translation)
        mock_message.answer.assert_called_once()
        mock_i18n.get.assert_any_call("word-not-found-enter-translation", word="unknownword")


class TestOnNoop:
    """Tests for on_noop handler."""

    async def test_answers_callback(
        self,
        mock_callback: MagicMock,
    ) -> None:
        """Handler answers callback."""
        await on_noop(mock_callback)

        mock_callback.answer.assert_called_once()
