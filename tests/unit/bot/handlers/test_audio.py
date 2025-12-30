"""Tests for audio handler."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.bot.handlers.audio import (
    _get_keyboard_for_context,
    on_audio_play,
)


class TestGetKeyboardForContext:
    """Tests for _get_keyboard_for_context helper."""

    def test_returns_learn_keyboard(self, mock_i18n: MagicMock) -> None:
        """Returns learning card keyboard for 'learn' context."""
        with patch("src.bot.handlers.audio.get_learning_card_keyboard") as mock_keyboard:
            mock_keyboard.return_value = MagicMock()

            result = _get_keyboard_for_context("learn", mock_i18n)

        mock_keyboard.assert_called_once_with(mock_i18n, word_id=None)
        assert result is not None

    def test_returns_review_keyboard(self, mock_i18n: MagicMock) -> None:
        """Returns review rating keyboard for 'review' context."""
        with patch("src.bot.handlers.audio.get_review_rating_keyboard") as mock_keyboard:
            mock_keyboard.return_value = MagicMock()

            result = _get_keyboard_for_context("review", mock_i18n)

        mock_keyboard.assert_called_once_with(mock_i18n, word_id=None)
        assert result is not None

    def test_returns_voice_keyboard(self, mock_i18n: MagicMock) -> None:
        """Returns voice prompt keyboard for 'voice' context."""
        with patch("src.bot.handlers.audio.get_voice_prompt_keyboard") as mock_keyboard:
            mock_keyboard.return_value = MagicMock()

            result = _get_keyboard_for_context("voice", mock_i18n)

        mock_keyboard.assert_called_once_with(mock_i18n, word_id=None)
        assert result is not None

    def test_returns_none_for_unknown_context(self, mock_i18n: MagicMock) -> None:
        """Returns None for unknown context."""
        result = _get_keyboard_for_context("unknown", mock_i18n)

        assert result is None


class TestOnAudioPlay:
    """Tests for on_audio_play handler."""

    async def test_returns_early_when_no_data_or_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
    ) -> None:
        """Handler returns early when no data or message."""
        mock_callback.data = None

        await on_audio_play(mock_callback, mock_i18n)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.data = "audio:play:learn:123"
        mock_callback.message = MagicMock()  # Not a Message instance

        await on_audio_play(mock_callback, mock_i18n)

        mock_callback.answer.assert_not_called()

    async def test_shows_error_when_invalid_callback_data(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows error for invalid callback data."""
        mock_callback.data = "audio:play:invalid"  # Missing word_id
        mock_callback.message = mock_message

        await on_audio_play(mock_callback, mock_i18n)

        mock_callback.answer.assert_called_once()
        mock_i18n.get.assert_any_call("audio-error")

    async def test_shows_loading_and_audio_not_available(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows audio not available message."""
        word_id = uuid4()
        mock_callback.data = f"audio:play:learn:{word_id}"
        mock_callback.message = mock_message
        mock_message.text = "Hello - привет"

        with patch("src.bot.handlers.audio.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.audio.AudioService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_audio_bytes = AsyncMock(return_value=None)

                await on_audio_play(mock_callback, mock_i18n)

        mock_i18n.get.assert_any_call("audio-not-available")

    async def test_plays_audio_successfully(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler plays audio successfully."""
        word_id = uuid4()
        mock_callback.data = f"audio:play:learn:{word_id}"
        mock_callback.message = mock_message
        mock_message.text = "Hello - привет"
        mock_message.delete = AsyncMock()
        mock_message.answer_audio = AsyncMock()

        audio_bytes = b"audio data"

        with patch("src.bot.handlers.audio.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.audio.AudioService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_audio_bytes = AsyncMock(return_value=audio_bytes)

                with patch("src.bot.handlers.audio._get_keyboard_for_context") as mock_keyboard:
                    mock_keyboard.return_value = MagicMock()

                    await on_audio_play(mock_callback, mock_i18n)

        mock_i18n.get.assert_any_call("audio-loading")
        mock_message.delete.assert_called_once()
        mock_message.answer_audio.assert_called_once()
