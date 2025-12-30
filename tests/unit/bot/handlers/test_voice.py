"""Tests for voice handler."""

from datetime import UTC, datetime
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.bot.handlers.voice import (
    VoiceStates,
    on_voice_message,
    on_voice_next,
    on_voice_retry,
    on_voice_start,
)
from src.modules.users.dto import UserReadDTO


class TestOnVoiceStart:
    """Tests for on_voice_start handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await on_voice_start(mock_callback, mock_i18n, db_user, mock_state)

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

        await on_voice_start(mock_callback, mock_i18n, db_user, mock_state)

        mock_callback.answer.assert_not_called()

    async def test_shows_no_words_message_when_empty(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows 'no words' when no words for pronunciation."""
        mock_callback.message = mock_message

        with (
            patch("src.bot.handlers.voice.AsyncSessionMaker") as mock_session_maker,
            patch("src.bot.handlers.voice.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit,
        ):
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.voice.VoiceService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_words_for_pronunciation = AsyncMock(return_value=[])

                await on_voice_start(mock_callback, mock_i18n, db_user, mock_state)

        mock_i18n.get.assert_any_call("voice-no-words")
        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()

    async def test_starts_session_when_words_available(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler starts voice session when words are available."""
        mock_callback.message = mock_message

        mock_word = MagicMock()
        mock_word.id = uuid4()
        mock_word.text = "hello"
        mock_word.phonetic = "/helo/"
        mock_word.language = "en"
        mock_word.model_dump = MagicMock(return_value={"id": str(mock_word.id), "text": "hello"})

        with (
            patch("src.bot.handlers.voice.AsyncSessionMaker") as mock_session_maker,
            patch("src.bot.handlers.voice._show_word_prompt", new_callable=AsyncMock) as mock_show,
        ):
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.voice.VoiceService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_words_for_pronunciation = AsyncMock(return_value=[mock_word])

                await on_voice_start(mock_callback, mock_i18n, db_user, mock_state)

        mock_state.update_data.assert_called_once()
        mock_state.set_state.assert_called_with(VoiceStates.waiting_for_voice)
        mock_show.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnVoiceRetry:
    """Tests for on_voice_retry handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await on_voice_retry(mock_callback, mock_i18n, mock_state)

        mock_state.get_data.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.message = MagicMock()

        await on_voice_retry(mock_callback, mock_i18n, mock_state)

        mock_state.get_data.assert_not_called()

    async def test_clears_state_when_no_words(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler clears state when no words in data."""
        mock_callback.message = mock_message
        mock_state.get_data = AsyncMock(return_value={"words": []})

        await on_voice_retry(mock_callback, mock_i18n, mock_state)

        mock_state.clear.assert_called_once()
        mock_callback.answer.assert_called_once()

    async def test_shows_word_prompt_for_retry(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows word prompt for retry."""
        mock_callback.message = mock_message

        word_id = str(uuid4())
        words = [{"id": word_id, "text": "hello", "phonetic": "/helo/", "language": "en"}]
        mock_state.get_data = AsyncMock(return_value={"words": words, "current_index": 0})

        with patch("src.bot.handlers.voice._show_word_prompt", new_callable=AsyncMock) as mock_show:
            await on_voice_retry(mock_callback, mock_i18n, mock_state)

        mock_state.set_state.assert_called_with(VoiceStates.waiting_for_voice)
        mock_show.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnVoiceNext:
    """Tests for on_voice_next handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await on_voice_next(mock_callback, mock_i18n, mock_state)

        mock_state.get_data.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.message = MagicMock()

        await on_voice_next(mock_callback, mock_i18n, mock_state)

        mock_state.get_data.assert_not_called()

    async def test_completes_session_with_stats_on_last_word(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler completes session with stats on last word."""
        mock_callback.message = mock_message
        mock_callback.data = "voice:next"

        log_id = str(uuid4())
        words = [{"id": str(uuid4()), "text": "hello"}]
        mock_state.get_data = AsyncMock(
            return_value={
                "words": words,
                "current_index": 0,
                "log_ids": [log_id],
                "session_start": datetime.now(tz=UTC).isoformat(),
            }
        )

        mock_stats = MagicMock()
        mock_stats.total_practiced = 1
        mock_stats.average_rating = 4.0
        mock_stats.time_spent_seconds = 120

        with (
            patch("src.bot.handlers.voice.AsyncSessionMaker") as mock_session_maker,
            patch("src.bot.handlers.voice.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit,
        ):
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.voice.VoiceService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_session_stats = AsyncMock(return_value=mock_stats)

                await on_voice_next(mock_callback, mock_i18n, mock_state)

        mock_state.clear.assert_called_once()
        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()

    async def test_completes_session_without_stats_when_no_logs(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler completes session without stats when no log IDs."""
        mock_callback.message = mock_message
        mock_callback.data = "voice:skip"

        words = [{"id": str(uuid4()), "text": "hello"}]
        mock_state.get_data = AsyncMock(
            return_value={
                "words": words,
                "current_index": 0,
                "log_ids": [],
                "session_start": datetime.now(tz=UTC).isoformat(),
            }
        )

        with patch("src.bot.handlers.voice.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit:
            await on_voice_next(mock_callback, mock_i18n, mock_state)

        mock_state.clear.assert_called_once()
        mock_safe_edit.assert_called_once()
        mock_i18n.get.assert_any_call("voice-session-ended")

    async def test_moves_to_next_word(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler moves to next word."""
        mock_callback.message = mock_message
        mock_callback.data = "voice:next"

        word_id_1 = str(uuid4())
        word_id_2 = str(uuid4())
        words = [
            {"id": word_id_1, "text": "hello", "phonetic": "/helo/", "language": "en"},
            {"id": word_id_2, "text": "world", "phonetic": "/world/", "language": "en"},
        ]
        mock_state.get_data = AsyncMock(
            return_value={
                "words": words,
                "current_index": 0,
                "log_ids": [],
            }
        )

        with patch("src.bot.handlers.voice._show_word_prompt", new_callable=AsyncMock) as mock_show:
            await on_voice_next(mock_callback, mock_i18n, mock_state)

        mock_state.update_data.assert_called_with(current_index=1)
        mock_state.set_state.assert_called_with(VoiceStates.waiting_for_voice)
        mock_show.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnVoiceMessage:
    """Tests for on_voice_message handler."""

    async def test_returns_early_when_no_voice(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when message has no voice."""
        mock_message.voice = None
        mock_message.bot = MagicMock()

        await on_voice_message(mock_message, mock_i18n, db_user, mock_state)

        mock_state.get_data.assert_not_called()

    async def test_returns_early_when_no_bot(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when message has no bot."""
        mock_message.voice = MagicMock()
        mock_message.bot = None

        await on_voice_message(mock_message, mock_i18n, db_user, mock_state)

        mock_state.get_data.assert_not_called()

    async def test_clears_state_when_no_words(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler clears state when no words in data."""
        mock_message.voice = MagicMock()
        mock_message.bot = MagicMock()
        mock_state.get_data = AsyncMock(return_value={"words": [], "current_index": 0})

        await on_voice_message(mock_message, mock_i18n, db_user, mock_state)

        mock_state.clear.assert_called_once()

    async def test_clears_state_when_index_out_of_range(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler clears state when current_index >= len(words)."""
        mock_message.voice = MagicMock()
        mock_message.bot = MagicMock()
        words = [{"id": str(uuid4()), "text": "hello"}]
        mock_state.get_data = AsyncMock(return_value={"words": words, "current_index": 1})

        await on_voice_message(mock_message, mock_i18n, db_user, mock_state)

        mock_state.clear.assert_called_once()

    async def test_handles_missing_file_path(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler handles case when file has no file_path."""
        mock_voice = MagicMock()
        mock_voice.file_id = "file123"
        mock_message.voice = mock_voice
        mock_message.bot = AsyncMock()
        mock_message.answer = AsyncMock()

        words = [{"id": str(uuid4()), "text": "hello", "language": "en"}]
        mock_state.get_data = AsyncMock(return_value={"words": words, "current_index": 0, "log_ids": []})

        mock_file = MagicMock()
        mock_file.file_path = None
        mock_message.bot.get_file = AsyncMock(return_value=mock_file)

        processing_msg = AsyncMock()
        mock_message.answer = AsyncMock(return_value=processing_msg)

        await on_voice_message(mock_message, mock_i18n, db_user, mock_state)

        mock_state.set_state.assert_called_with(VoiceStates.waiting_for_voice)
        processing_msg.edit_text.assert_called_once()

    async def test_handles_non_bytesio_file_data(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler handles case when file_data is not BytesIO."""
        mock_voice = MagicMock()
        mock_voice.file_id = "file123"
        mock_message.voice = mock_voice
        mock_message.bot = AsyncMock()

        words = [{"id": str(uuid4()), "text": "hello", "language": "en"}]
        mock_state.get_data = AsyncMock(return_value={"words": words, "current_index": 0, "log_ids": []})

        mock_file = MagicMock()
        mock_file.file_path = "/path/to/file.ogg"
        mock_message.bot.get_file = AsyncMock(return_value=mock_file)
        # Return something that's not BytesIO
        mock_message.bot.download_file = AsyncMock(return_value="not a BytesIO")

        processing_msg = AsyncMock()
        mock_message.answer = AsyncMock(return_value=processing_msg)

        await on_voice_message(mock_message, mock_i18n, db_user, mock_state)

        mock_state.set_state.assert_called_with(VoiceStates.waiting_for_voice)
        processing_msg.edit_text.assert_called_once()

    async def test_processes_voice_successfully(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler processes voice message successfully."""
        mock_voice = MagicMock()
        mock_voice.file_id = "file123"
        mock_message.voice = mock_voice
        mock_message.bot = AsyncMock()

        word_id = str(uuid4())
        words = [{"id": word_id, "text": "hello", "language": "en", "phonetic": "/helo/"}]
        mock_state.get_data = AsyncMock(return_value={"words": words, "current_index": 0, "log_ids": []})

        mock_file = MagicMock()
        mock_file.file_path = "/path/to/file.ogg"
        mock_message.bot.get_file = AsyncMock(return_value=mock_file)

        # Return BytesIO
        audio_data = BytesIO(b"audio data")
        mock_message.bot.download_file = AsyncMock(return_value=audio_data)

        processing_msg = AsyncMock()
        mock_message.answer = AsyncMock(return_value=processing_msg)

        mock_log = MagicMock()
        mock_log.id = uuid4()
        mock_log.rating = 4
        mock_log.transcribed_text = "hello"
        mock_log.feedback = "Good pronunciation!"

        with (
            patch("src.bot.handlers.voice.AsyncSessionMaker") as mock_session_maker,
        ):
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.voice.VoiceService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.process_voice_message = AsyncMock(return_value=mock_log)

                await on_voice_message(mock_message, mock_i18n, db_user, mock_state)

        mock_state.update_data.assert_called()
        mock_state.set_state.assert_called_with(VoiceStates.showing_result)
        processing_msg.edit_text.assert_called()

    async def test_handles_exception(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler handles exception during processing."""
        from aiogram.exceptions import TelegramBadRequest

        mock_voice = MagicMock()
        mock_voice.file_id = "file123"
        mock_message.voice = mock_voice
        mock_message.bot = AsyncMock()

        word_id = str(uuid4())
        words = [{"id": word_id, "text": "hello", "language": "en"}]
        mock_state.get_data = AsyncMock(return_value={"words": words, "current_index": 0, "log_ids": []})

        mock_file = MagicMock()
        mock_file.file_path = "/path/to/file.ogg"
        mock_message.bot.get_file = AsyncMock(return_value=mock_file)

        audio_data = BytesIO(b"audio data")
        mock_message.bot.download_file = AsyncMock(return_value=audio_data)

        processing_msg = AsyncMock()
        mock_message.answer = AsyncMock(return_value=processing_msg)

        with (
            patch("src.bot.handlers.voice.AsyncSessionMaker") as mock_session_maker,
        ):
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.voice.VoiceService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.process_voice_message = AsyncMock(
                    side_effect=TelegramBadRequest(method=MagicMock(), message="Bad request")
                )

                await on_voice_message(mock_message, mock_i18n, db_user, mock_state)

        mock_state.set_state.assert_called_with(VoiceStates.waiting_for_voice)
        processing_msg.edit_text.assert_called()
