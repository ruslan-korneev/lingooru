"""Tests for learn handler."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.bot.handlers.learn import (
    LearnStates,
    _start_learning_session,
    on_learn_action,
    on_learn_language_selected,
    on_learn_start,
    on_translation_input,
    on_word_add_prompt,
)
from src.modules.users.dto import UserReadDTO
from src.modules.vocabulary.enums import Language


class TestOnLearnStart:
    """Tests for on_learn_start handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await on_learn_start(mock_callback, mock_i18n, db_user, mock_state)

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

        await on_learn_start(mock_callback, mock_i18n, db_user, mock_state)

        mock_callback.answer.assert_not_called()

    async def test_shows_no_words_message_when_count_zero(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows 'no words' when count is 0."""
        mock_callback.message = mock_message

        with (
            patch("src.bot.handlers.learn.AsyncSessionMaker") as mock_session_maker,
            patch("src.bot.handlers.learn.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit,
        ):
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.learn.VocabularyService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.count_unlearned_for_language = AsyncMock(return_value=0)

                await on_learn_start(mock_callback, mock_i18n, db_user, mock_state)

        mock_i18n.get.assert_any_call("learn-no-words-for-pair")
        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()

    async def test_starts_learning_session_when_words_available(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler starts learning session when words are available."""
        mock_callback.message = mock_message

        with (
            patch("src.bot.handlers.learn.AsyncSessionMaker") as mock_session_maker,
            patch("src.bot.handlers.learn._start_learning_session", new_callable=AsyncMock) as mock_start,
        ):
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.learn.VocabularyService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.count_unlearned_for_language = AsyncMock(return_value=5)

                await on_learn_start(mock_callback, mock_i18n, db_user, mock_state)

        mock_start.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnLearnLanguageSelected:
    """Tests for on_learn_language_selected handler."""

    async def test_returns_early_when_no_data_or_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when no data or message."""
        mock_callback.data = None

        await on_learn_language_selected(mock_callback, mock_i18n, db_user, mock_state)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.data = "learn:lang:en"
        mock_callback.message = MagicMock()

        await on_learn_language_selected(mock_callback, mock_i18n, db_user, mock_state)

        mock_callback.answer.assert_not_called()

    async def test_selects_english_language(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler selects English language."""
        mock_callback.data = "learn:lang:en"
        mock_callback.message = mock_message

        with patch("src.bot.handlers.learn._start_learning_session", new_callable=AsyncMock) as mock_start:
            await on_learn_language_selected(mock_callback, mock_i18n, db_user, mock_state)

        mock_start.assert_called_once()
        # Check that source_language is Language.EN
        call_kwargs = mock_start.call_args.kwargs
        assert call_kwargs["source_language"] is Language.EN
        mock_callback.answer.assert_called_once()

    async def test_selects_korean_language(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler selects Korean language."""
        mock_callback.data = "learn:lang:ko"
        mock_callback.message = mock_message

        with patch("src.bot.handlers.learn._start_learning_session", new_callable=AsyncMock) as mock_start:
            await on_learn_language_selected(mock_callback, mock_i18n, db_user, mock_state)

        call_kwargs = mock_start.call_args.kwargs
        assert call_kwargs["source_language"] is Language.KO
        mock_callback.answer.assert_called_once()

    async def test_selects_mix_all_languages(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler selects all languages (mix)."""
        mock_callback.data = "learn:lang:mix"
        mock_callback.message = mock_message

        with patch("src.bot.handlers.learn._start_learning_session", new_callable=AsyncMock) as mock_start:
            await on_learn_language_selected(mock_callback, mock_i18n, db_user, mock_state)

        call_kwargs = mock_start.call_args.kwargs
        assert call_kwargs["source_language"] is None
        mock_callback.answer.assert_called_once()


class TestStartLearningSession:
    """Tests for _start_learning_session helper."""

    async def test_shows_no_words_message_when_empty(
        self,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Shows 'no words' when no words for learning."""
        with (
            patch("src.bot.handlers.learn.AsyncSessionMaker") as mock_session_maker,
            patch("src.bot.handlers.learn.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit,
        ):
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.learn.VocabularyService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_words_for_learning = AsyncMock(return_value=[])

                await _start_learning_session(mock_message, mock_i18n, db_user, mock_state, Language.EN)

        mock_i18n.get.assert_any_call("learn-no-words")
        mock_safe_edit.assert_called_once()

    async def test_starts_session_and_shows_first_word(
        self,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Starts session and shows first word."""
        mock_word = MagicMock()
        mock_word.word.id = MagicMock()
        mock_word.word.text = "hello"
        mock_word.word.translation = "привет"
        mock_word.word.phonetic = None
        mock_word.word.example_sentence = None
        mock_word.word.language = Language.EN
        mock_word.model_dump = MagicMock(return_value={"id": "123", "word": {}})

        with (
            patch("src.bot.handlers.learn.AsyncSessionMaker") as mock_session_maker,
            patch("src.bot.handlers.learn.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit,
        ):
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.learn.VocabularyService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_words_for_learning = AsyncMock(return_value=[mock_word])

                await _start_learning_session(mock_message, mock_i18n, db_user, mock_state, Language.EN)

        mock_state.update_data.assert_called_once()
        mock_state.set_state.assert_called_with(LearnStates.learning_session)
        mock_safe_edit.assert_called_once()


class TestOnLearnAction:
    """Tests for on_learn_action handler."""

    async def test_returns_early_when_no_data_or_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when no data or message."""
        mock_callback.data = None

        await on_learn_action(mock_callback, mock_i18n, db_user, mock_state)

        mock_state.get_data.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.data = "learn:know"
        mock_callback.message = MagicMock()

        await on_learn_action(mock_callback, mock_i18n, db_user, mock_state)

        mock_state.get_data.assert_not_called()

    async def test_clears_state_when_no_words(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler clears state when no words in data."""
        mock_callback.data = "learn:know"
        mock_callback.message = mock_message
        mock_state.get_data = AsyncMock(return_value={"learning_words": []})

        await on_learn_action(mock_callback, mock_i18n, db_user, mock_state)

        mock_state.clear.assert_called_once()
        mock_callback.answer.assert_called_once()

    async def test_marks_word_as_learned_on_know(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler marks word as learned on 'know' action."""
        mock_callback.data = "learn:know"
        mock_callback.message = mock_message

        word_id_1 = str(uuid4())
        word_id_2 = str(uuid4())
        word_data = [
            {"id": word_id_1, "word": {"id": word_id_1, "text": "hello", "translation": "привет", "language": "en"}},
            {"id": word_id_2, "word": {"id": word_id_2, "text": "world", "translation": "мир", "language": "en"}},
        ]
        mock_state.get_data = AsyncMock(return_value={"learning_words": word_data, "current_index": 0})

        with (
            patch("src.bot.handlers.learn.AsyncSessionMaker") as mock_session_maker,
            patch("src.bot.handlers.learn.safe_edit_or_send", new_callable=AsyncMock),
        ):
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with (
                patch("src.bot.handlers.learn.VocabularyService") as mock_vocab_service_class,
                patch("src.bot.handlers.learn.SRSService") as mock_srs_service_class,
            ):
                mock_vocab_service = mock_vocab_service_class.return_value
                mock_vocab_service.mark_word_learned = AsyncMock()

                mock_srs_service = mock_srs_service_class.return_value
                mock_srs_service.get_or_create_review = AsyncMock()

                await on_learn_action(mock_callback, mock_i18n, db_user, mock_state)

        mock_vocab_service.mark_word_learned.assert_called_once()
        mock_srs_service.get_or_create_review.assert_called_once()

    async def test_completes_session_on_last_word(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler completes session on last word."""
        mock_callback.data = "learn:skip"
        mock_callback.message = mock_message

        word_id = str(uuid4())
        word_data = [
            {"id": word_id, "word": {"id": word_id, "text": "hello", "translation": "привет", "language": "en"}}
        ]
        mock_state.get_data = AsyncMock(return_value={"learning_words": word_data, "current_index": 0})

        with patch("src.bot.handlers.learn.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit:
            await on_learn_action(mock_callback, mock_i18n, db_user, mock_state)

        mock_state.clear.assert_called_once()
        mock_safe_edit.assert_called_once()
        mock_i18n.get.assert_any_call("learn-session-complete", count=1)


class TestOnWordAddPrompt:
    """Tests for on_word_add_prompt handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
    ) -> None:
        """Handler returns early when no message."""
        mock_callback.message = None

        await on_word_add_prompt(mock_callback, mock_i18n)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.message = MagicMock()

        await on_word_add_prompt(mock_callback, mock_i18n)

        mock_callback.answer.assert_not_called()

    async def test_shows_add_prompt(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows word add prompt."""
        mock_callback.message = mock_message

        with patch("src.bot.handlers.learn.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit:
            await on_word_add_prompt(mock_callback, mock_i18n)

        mock_i18n.get.assert_any_call("word-add-prompt")
        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnTranslationInput:
    """Tests for on_translation_input handler."""

    async def test_clears_state_when_no_pending_word(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler clears state when no pending word."""
        mock_state.get_data = AsyncMock(return_value={})
        mock_message.text = "перевод"

        await on_translation_input(mock_message, mock_i18n, db_user, mock_state)

        mock_state.clear.assert_called_once()

    async def test_clears_state_when_no_text(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler clears state when no message text."""
        mock_state.get_data = AsyncMock(return_value={"pending_word": "hello"})
        mock_message.text = None

        await on_translation_input(mock_message, mock_i18n, db_user, mock_state)

        mock_state.clear.assert_called_once()

    async def test_adds_word_with_translation(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler adds word with provided translation."""
        mock_state.get_data = AsyncMock(return_value={"pending_word": "hello"})
        mock_message.text = "привет"

        mock_user_word = MagicMock()
        mock_user_word.word.text = "hello"
        mock_user_word.word.translation = "привет"
        mock_user_word.word.phonetic = None

        with patch("src.bot.handlers.learn.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.learn.VocabularyService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.add_word_with_translation = AsyncMock(return_value=mock_user_word)

                await on_translation_input(mock_message, mock_i18n, db_user, mock_state)

        mock_service.add_word_with_translation.assert_called_once()
        mock_state.clear.assert_called_once()
        mock_message.answer.assert_called_once()
