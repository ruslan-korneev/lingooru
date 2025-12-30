"""Tests for word lists keyboards."""

from unittest.mock import MagicMock

from aiogram_i18n import I18nContext

from src.bot.keyboards.word_lists import (
    get_list_added_keyboard,
    get_word_list_preview_keyboard,
    get_word_lists_keyboard,
)
from src.modules.vocabulary.word_lists import ThematicWordList

# Expected keyboard row counts
ROWS_MENU_ONLY = 1
ROWS_WITH_MENU = 2
ROWS_TWO_LISTS_MENU = 3


def create_mock_i18n() -> MagicMock:
    """Create a mock I18nContext."""
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(side_effect=lambda key, **_: f"[{key}]")
    return i18n


def create_mock_word_list(list_id: str, name_en: str, name_ru: str) -> ThematicWordList:
    """Create a mock ThematicWordList."""
    wl = MagicMock(spec=ThematicWordList)
    wl.id = list_id
    wl.get_name = MagicMock(side_effect=lambda lang: name_en if lang == "en" else name_ru)
    return wl


class TestGetWordListsKeyboard:
    """Tests for get_word_lists_keyboard function."""

    def test_empty_lists(self) -> None:
        """Returns keyboard with only back button when no lists."""
        i18n = create_mock_i18n()

        keyboard = get_word_lists_keyboard(i18n, word_lists=[], lang="en")

        # Should only have back button
        assert len(keyboard.inline_keyboard) == ROWS_MENU_ONLY
        assert keyboard.inline_keyboard[0][0].callback_data == "menu:main"

    def test_shows_word_lists(self) -> None:
        """Shows word list buttons with correct callback data."""
        i18n = create_mock_i18n()
        lists = [
            create_mock_word_list("food", "Food", "Еда"),
            create_mock_word_list("animals", "Animals", "Животные"),
        ]

        keyboard = get_word_lists_keyboard(i18n, word_lists=lists, lang="en")

        # Should have list buttons + back button
        assert len(keyboard.inline_keyboard) == ROWS_TWO_LISTS_MENU
        assert keyboard.inline_keyboard[0][0].text == "Food"
        assert keyboard.inline_keyboard[0][0].callback_data == "lists:preview:food"
        assert keyboard.inline_keyboard[1][0].text == "Animals"
        assert keyboard.inline_keyboard[1][0].callback_data == "lists:preview:animals"
        assert keyboard.inline_keyboard[2][0].callback_data == "menu:main"

    def test_marks_added_lists_with_checkmark(self) -> None:
        """Shows checkmark for lists already added by user."""
        i18n = create_mock_i18n()
        lists = [
            create_mock_word_list("food", "Food", "Еда"),
            create_mock_word_list("animals", "Animals", "Животные"),
        ]

        keyboard = get_word_lists_keyboard(
            i18n,
            word_lists=lists,
            lang="en",
            added_list_ids={"food"},  # Food list is already added
        )

        # Food should have checkmark
        assert keyboard.inline_keyboard[0][0].text == "✅ Food"
        # Animals should not
        assert keyboard.inline_keyboard[1][0].text == "Animals"

    def test_uses_correct_language(self) -> None:
        """Uses correct language for list names."""
        i18n = create_mock_i18n()
        lists = [
            create_mock_word_list("food", "Food", "Еда"),
        ]

        keyboard = get_word_lists_keyboard(i18n, word_lists=lists, lang="ru")

        assert keyboard.inline_keyboard[0][0].text == "Еда"

    def test_handles_none_added_list_ids(self) -> None:
        """Handles None added_list_ids correctly."""
        i18n = create_mock_i18n()
        lists = [
            create_mock_word_list("food", "Food", "Еда"),
        ]

        # Should not raise with None (default)
        keyboard = get_word_lists_keyboard(i18n, word_lists=lists, lang="en")

        assert keyboard.inline_keyboard[0][0].text == "Food"


class TestGetWordListPreviewKeyboard:
    """Tests for get_word_list_preview_keyboard function."""

    def test_not_added_shows_add_button(self) -> None:
        """Shows add button when list not already added."""
        i18n = create_mock_i18n()

        keyboard = get_word_list_preview_keyboard(i18n, list_id="food", is_added=False)

        assert len(keyboard.inline_keyboard) == ROWS_WITH_MENU
        # First row: Add list button
        assert keyboard.inline_keyboard[0][0].callback_data == "lists:add:food"
        assert "[btn-add-list]" in keyboard.inline_keyboard[0][0].text
        # Second row: Back button
        assert keyboard.inline_keyboard[1][0].callback_data == "lists:show"

    def test_already_added_shows_added_status(self) -> None:
        """Shows 'already added' status when list is already added."""
        i18n = create_mock_i18n()

        keyboard = get_word_list_preview_keyboard(i18n, list_id="food", is_added=True)

        assert len(keyboard.inline_keyboard) == ROWS_WITH_MENU
        # First row: Already added status (noop callback)
        assert keyboard.inline_keyboard[0][0].callback_data == "noop"
        assert "[btn-list-added]" in keyboard.inline_keyboard[0][0].text
        # Second row: Back button
        assert keyboard.inline_keyboard[1][0].callback_data == "lists:show"


class TestGetListAddedKeyboard:
    """Tests for get_list_added_keyboard function."""

    def test_keyboard_structure(self) -> None:
        """Creates keyboard with learn, more lists, and menu buttons."""
        i18n = create_mock_i18n()

        keyboard = get_list_added_keyboard(i18n)

        assert len(keyboard.inline_keyboard) == ROWS_WITH_MENU
        # First row: Learn, More lists
        assert keyboard.inline_keyboard[0][0].callback_data == "learn:start"
        assert keyboard.inline_keyboard[0][1].callback_data == "lists:show"
        # Second row: Menu
        assert keyboard.inline_keyboard[1][0].callback_data == "menu:main"
