"""Tests for learn keyboards."""

from unittest.mock import MagicMock
from uuid import uuid4

from aiogram_i18n import I18nContext

from src.bot.keyboards.learn import (
    get_language_selection_keyboard,
    get_learning_card_keyboard,
    get_learning_complete_keyboard,
    get_word_added_keyboard,
    get_word_not_found_keyboard,
)
from src.modules.vocabulary.models import Language

# Expected keyboard row counts
ROWS_MENU_ONLY = 1
ROWS_WITH_MENU = 2
ROWS_LANG_MIX_MENU = 3
ROWS_TWO_LANGS_MIX_MENU = 4

# Rating buttons count
RATING_BUTTONS = 3

# Test word counts
WORD_COUNT_EN = 5
WORD_COUNT_KO = 3
WORD_COUNT_TOTAL = 8


def create_mock_i18n() -> MagicMock:
    """Create a mock I18nContext."""
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(side_effect=lambda key, **_: f"[{key}]")
    return i18n


class TestGetLanguageSelectionKeyboard:
    """Tests for get_language_selection_keyboard function."""

    def test_no_languages(self) -> None:
        """Returns keyboard with only menu button when no words."""
        i18n = create_mock_i18n()
        counts: dict[Language, int] = {}

        keyboard = get_language_selection_keyboard(i18n, counts)

        # Should only have menu button
        assert len(keyboard.inline_keyboard) == ROWS_MENU_ONLY
        assert keyboard.inline_keyboard[0][0].callback_data == "menu:main"

    def test_only_english(self) -> None:
        """Shows English button when only English words exist."""
        i18n = create_mock_i18n()
        counts = {Language.EN: WORD_COUNT_EN}

        keyboard = get_language_selection_keyboard(i18n, counts)

        # Should have EN, Mix, and Menu buttons
        assert len(keyboard.inline_keyboard) == ROWS_LANG_MIX_MENU
        assert "English" in keyboard.inline_keyboard[0][0].text
        assert keyboard.inline_keyboard[0][0].callback_data == "learn:lang:en"
        assert keyboard.inline_keyboard[1][0].callback_data == "learn:lang:mix"

    def test_only_korean(self) -> None:
        """Shows Korean button when only Korean words exist."""
        i18n = create_mock_i18n()
        counts = {Language.KO: WORD_COUNT_KO}

        keyboard = get_language_selection_keyboard(i18n, counts)

        # Should have KO, Mix, and Menu buttons
        assert len(keyboard.inline_keyboard) == ROWS_LANG_MIX_MENU
        assert "Korean" in keyboard.inline_keyboard[0][0].text
        assert keyboard.inline_keyboard[0][0].callback_data == "learn:lang:ko"
        assert keyboard.inline_keyboard[1][0].callback_data == "learn:lang:mix"

    def test_both_languages(self) -> None:
        """Shows both language buttons when both exist."""
        i18n = create_mock_i18n()
        counts = {Language.EN: WORD_COUNT_EN, Language.KO: WORD_COUNT_KO}

        keyboard = get_language_selection_keyboard(i18n, counts)

        # Should have EN, KO, Mix, and Menu buttons
        assert len(keyboard.inline_keyboard) == ROWS_TWO_LANGS_MIX_MENU
        assert "English" in keyboard.inline_keyboard[0][0].text
        assert "Korean" in keyboard.inline_keyboard[1][0].text
        assert keyboard.inline_keyboard[2][0].callback_data == "learn:lang:mix"
        assert keyboard.inline_keyboard[3][0].callback_data == "menu:main"

    def test_zero_counts_not_shown(self) -> None:
        """Languages with zero count are not shown."""
        i18n = create_mock_i18n()
        counts = {Language.EN: 0, Language.KO: WORD_COUNT_EN}

        keyboard = get_language_selection_keyboard(i18n, counts)

        # Should only have KO, Mix, and Menu buttons
        assert len(keyboard.inline_keyboard) == ROWS_LANG_MIX_MENU
        assert "Korean" in keyboard.inline_keyboard[0][0].text
        assert keyboard.inline_keyboard[1][0].callback_data == "learn:lang:mix"

    def test_total_shown_in_mix(self) -> None:
        """Mix button shows total word count."""
        i18n = create_mock_i18n()
        counts = {Language.EN: WORD_COUNT_EN, Language.KO: WORD_COUNT_KO}

        keyboard = get_language_selection_keyboard(i18n, counts)

        # Find mix button and check total
        mix_row = keyboard.inline_keyboard[2]
        assert f"({WORD_COUNT_TOTAL})" in mix_row[0].text


class TestGetLearningCardKeyboard:
    """Tests for get_learning_card_keyboard function."""

    def test_without_word_id(self) -> None:
        """Creates keyboard without audio button when no word_id."""
        i18n = create_mock_i18n()

        keyboard = get_learning_card_keyboard(i18n)

        # Should not have audio button, only rating and navigation
        assert len(keyboard.inline_keyboard) == ROWS_WITH_MENU
        # First row: Know, Hard, Forgot
        assert len(keyboard.inline_keyboard[0]) == RATING_BUTTONS
        assert keyboard.inline_keyboard[0][0].callback_data == "learn:know"
        # Second row: Skip, Menu
        assert keyboard.inline_keyboard[1][0].callback_data == "learn:skip"

    def test_with_word_id(self) -> None:
        """Creates keyboard with audio button when word_id provided."""
        i18n = create_mock_i18n()
        word_id = uuid4()

        keyboard = get_learning_card_keyboard(i18n, word_id=word_id)

        # Should have audio button as first row
        assert len(keyboard.inline_keyboard) == ROWS_LANG_MIX_MENU
        assert f"audio:play:learn:{word_id}" == keyboard.inline_keyboard[0][0].callback_data
        # Second row: Know, Hard, Forgot
        assert keyboard.inline_keyboard[1][0].callback_data == "learn:know"


class TestGetWordAddedKeyboard:
    """Tests for get_word_added_keyboard function."""

    def test_keyboard_structure(self) -> None:
        """Creates keyboard with learn and add more buttons."""
        i18n = create_mock_i18n()

        keyboard = get_word_added_keyboard(i18n)

        assert len(keyboard.inline_keyboard) == ROWS_WITH_MENU
        # First row: Learn, Add more
        assert keyboard.inline_keyboard[0][0].callback_data == "learn:start"
        assert keyboard.inline_keyboard[0][1].callback_data == "word:add"
        # Second row: Menu
        assert keyboard.inline_keyboard[1][0].callback_data == "menu:main"


class TestGetWordNotFoundKeyboard:
    """Tests for get_word_not_found_keyboard function."""

    def test_keyboard_structure(self) -> None:
        """Creates keyboard with add words and lists buttons."""
        i18n = create_mock_i18n()

        keyboard = get_word_not_found_keyboard(i18n)

        assert len(keyboard.inline_keyboard) == ROWS_WITH_MENU
        # First row: Add words, Word lists
        assert keyboard.inline_keyboard[0][0].callback_data == "word:add"
        assert keyboard.inline_keyboard[0][1].callback_data == "lists:show"
        # Second row: Menu
        assert keyboard.inline_keyboard[1][0].callback_data == "menu:main"


class TestGetLearningCompleteKeyboard:
    """Tests for get_learning_complete_keyboard function."""

    def test_keyboard_structure(self) -> None:
        """Creates keyboard with learn again and add words buttons."""
        i18n = create_mock_i18n()

        keyboard = get_learning_complete_keyboard(i18n)

        assert len(keyboard.inline_keyboard) == ROWS_WITH_MENU
        # First row: Learn again, Add words
        assert keyboard.inline_keyboard[0][0].callback_data == "learn:start"
        assert keyboard.inline_keyboard[0][1].callback_data == "word:add"
        # Second row: Menu
        assert keyboard.inline_keyboard[1][0].callback_data == "menu:main"
