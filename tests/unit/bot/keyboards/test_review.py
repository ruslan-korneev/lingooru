"""Tests for review keyboards."""

from unittest.mock import MagicMock
from uuid import uuid4

from aiogram_i18n import I18nContext

from src.bot.keyboards.review import (
    get_review_complete_keyboard,
    get_review_rating_keyboard,
    get_review_show_answer_keyboard,
    get_review_start_keyboard,
)

# Expected keyboard row counts
ROWS_WITH_MENU = 2
ROWS_WITH_AUDIO = 3

# Rating buttons count
RATING_BUTTONS = 5


def create_mock_i18n() -> MagicMock:
    """Create a mock I18nContext."""
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(side_effect=lambda key, **_: f"[{key}]")
    return i18n


class TestGetReviewStartKeyboard:
    """Tests for get_review_start_keyboard function."""

    def test_keyboard_structure(self) -> None:
        """Creates keyboard with begin review and menu buttons."""
        i18n = create_mock_i18n()

        keyboard = get_review_start_keyboard(i18n)

        assert len(keyboard.inline_keyboard) == ROWS_WITH_MENU
        # First row: Begin review
        assert keyboard.inline_keyboard[0][0].callback_data == "review:begin"
        # Second row: Menu
        assert keyboard.inline_keyboard[1][0].callback_data == "menu:main"


class TestGetReviewShowAnswerKeyboard:
    """Tests for get_review_show_answer_keyboard function."""

    def test_keyboard_structure(self) -> None:
        """Creates keyboard with show answer and menu buttons."""
        i18n = create_mock_i18n()

        keyboard = get_review_show_answer_keyboard(i18n)

        assert len(keyboard.inline_keyboard) == ROWS_WITH_MENU
        # First row: Show answer
        assert keyboard.inline_keyboard[0][0].callback_data == "review:show"
        # Second row: Menu
        assert keyboard.inline_keyboard[1][0].callback_data == "menu:main"


class TestGetReviewRatingKeyboard:
    """Tests for get_review_rating_keyboard function."""

    def test_without_word_id(self) -> None:
        """Creates keyboard without audio button when no word_id."""
        i18n = create_mock_i18n()

        keyboard = get_review_rating_keyboard(i18n)

        # Should have rating row and menu row (no audio button)
        assert len(keyboard.inline_keyboard) == ROWS_WITH_MENU
        # First row: Rating buttons 1-5
        assert len(keyboard.inline_keyboard[0]) == RATING_BUTTONS
        assert keyboard.inline_keyboard[0][0].callback_data == "review:rate:1"
        assert keyboard.inline_keyboard[0][4].callback_data == "review:rate:5"
        # Second row: Menu
        assert keyboard.inline_keyboard[1][0].callback_data == "menu:main"

    def test_with_word_id(self) -> None:
        """Creates keyboard with audio button when word_id provided."""
        i18n = create_mock_i18n()
        word_id = uuid4()

        keyboard = get_review_rating_keyboard(i18n, word_id=word_id)

        # Should have audio, rating, and menu rows
        assert len(keyboard.inline_keyboard) == ROWS_WITH_AUDIO
        # First row: Audio button
        assert f"audio:play:review:{word_id}" == keyboard.inline_keyboard[0][0].callback_data
        # Second row: Rating buttons 1-5
        assert len(keyboard.inline_keyboard[1]) == RATING_BUTTONS
        assert keyboard.inline_keyboard[1][0].callback_data == "review:rate:1"
        # Third row: Menu
        assert keyboard.inline_keyboard[2][0].callback_data == "menu:main"

    def test_rating_buttons_text(self) -> None:
        """Rating buttons show emoji numbers."""
        i18n = create_mock_i18n()

        keyboard = get_review_rating_keyboard(i18n)

        rating_row = keyboard.inline_keyboard[0]
        assert rating_row[0].text == "1️⃣"
        assert rating_row[1].text == "2️⃣"
        assert rating_row[2].text == "3️⃣"
        assert rating_row[3].text == "4️⃣"
        assert rating_row[4].text == "5️⃣"


class TestGetReviewCompleteKeyboard:
    """Tests for get_review_complete_keyboard function."""

    def test_keyboard_structure(self) -> None:
        """Creates keyboard with review again, learn, and menu buttons."""
        i18n = create_mock_i18n()

        keyboard = get_review_complete_keyboard(i18n)

        assert len(keyboard.inline_keyboard) == ROWS_WITH_MENU
        # First row: Review again, Learn
        assert keyboard.inline_keyboard[0][0].callback_data == "review:start"
        assert keyboard.inline_keyboard[0][1].callback_data == "learn:start"
        # Second row: Menu
        assert keyboard.inline_keyboard[1][0].callback_data == "menu:main"
