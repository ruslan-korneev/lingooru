"""Tests for voice keyboards."""

from unittest.mock import MagicMock
from uuid import uuid4

from aiogram_i18n import I18nContext

from src.bot.keyboards.voice import (
    get_voice_complete_keyboard,
    get_voice_no_words_keyboard,
    get_voice_prompt_keyboard,
    get_voice_result_keyboard,
)

# Expected keyboard row counts
ROWS_WITH_MENU = 2
ROWS_WITH_AUDIO = 3


def create_mock_i18n() -> MagicMock:
    """Create a mock I18nContext."""
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(side_effect=lambda key, **_: f"[{key}]")
    return i18n


class TestGetVoicePromptKeyboard:
    """Tests for get_voice_prompt_keyboard function."""

    def test_without_word_id(self) -> None:
        """Creates keyboard without audio button when no word_id."""
        i18n = create_mock_i18n()

        keyboard = get_voice_prompt_keyboard(i18n)

        # Should have skip and menu buttons only
        assert len(keyboard.inline_keyboard) == ROWS_WITH_MENU
        assert keyboard.inline_keyboard[0][0].callback_data == "voice:skip"
        assert keyboard.inline_keyboard[1][0].callback_data == "menu:main"

    def test_with_word_id(self) -> None:
        """Creates keyboard with audio button when word_id provided."""
        i18n = create_mock_i18n()
        word_id = uuid4()

        keyboard = get_voice_prompt_keyboard(i18n, word_id=word_id)

        # Should have audio, skip, and menu buttons
        assert len(keyboard.inline_keyboard) == ROWS_WITH_AUDIO
        assert f"audio:play:voice:{word_id}" == keyboard.inline_keyboard[0][0].callback_data
        assert keyboard.inline_keyboard[1][0].callback_data == "voice:skip"
        assert keyboard.inline_keyboard[2][0].callback_data == "menu:main"


class TestGetVoiceResultKeyboard:
    """Tests for get_voice_result_keyboard function."""

    def test_keyboard_structure(self) -> None:
        """Creates result keyboard with retry and next buttons."""
        i18n = create_mock_i18n()

        keyboard = get_voice_result_keyboard(i18n)

        assert len(keyboard.inline_keyboard) == ROWS_WITH_MENU
        # First row: Retry, Next
        assert keyboard.inline_keyboard[0][0].callback_data == "voice:retry"
        assert keyboard.inline_keyboard[0][1].callback_data == "voice:next"
        # Second row: Menu
        assert keyboard.inline_keyboard[1][0].callback_data == "menu:main"


class TestGetVoiceCompleteKeyboard:
    """Tests for get_voice_complete_keyboard function."""

    def test_keyboard_structure(self) -> None:
        """Creates complete keyboard with voice again and learn buttons."""
        i18n = create_mock_i18n()

        keyboard = get_voice_complete_keyboard(i18n)

        assert len(keyboard.inline_keyboard) == ROWS_WITH_MENU
        # First row: Voice again, Learn
        assert keyboard.inline_keyboard[0][0].callback_data == "voice:start"
        assert keyboard.inline_keyboard[0][1].callback_data == "learn:start"
        # Second row: Menu
        assert keyboard.inline_keyboard[1][0].callback_data == "menu:main"


class TestGetVoiceNoWordsKeyboard:
    """Tests for get_voice_no_words_keyboard function."""

    def test_keyboard_structure(self) -> None:
        """Creates no-words keyboard with add and learn buttons."""
        i18n = create_mock_i18n()

        keyboard = get_voice_no_words_keyboard(i18n)

        assert len(keyboard.inline_keyboard) == ROWS_WITH_MENU
        # First row: Add words, Learn
        assert keyboard.inline_keyboard[0][0].callback_data == "word:add"
        assert keyboard.inline_keyboard[0][1].callback_data == "learn:start"
        # Second row: Menu
        assert keyboard.inline_keyboard[1][0].callback_data == "menu:main"
