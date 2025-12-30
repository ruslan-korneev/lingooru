"""Tests for vocabulary keyboards."""

from unittest.mock import MagicMock

from aiogram_i18n import I18nContext

from src.bot.keyboards.vocabulary import (
    get_vocabulary_keyboard,
    get_vocabulary_pagination_keyboard,
)
from src.modules.vocabulary.enums import Language

# Expected keyboard row counts
ROWS_WITH_MENU = 2

# Navigation button counts
NAV_BUTTONS_FIRST_PAGE = 2
NAV_BUTTONS_LAST_PAGE = 2
NAV_BUTTONS_MIDDLE_PAGE = 3
NAV_BUTTONS_SINGLE_PAGE = 1

# Test page counts
TOTAL_PAGES_THREE = 3
TOTAL_PAGES_FIVE = 5
TOTAL_PAGES_ONE = 1


def create_mock_i18n() -> MagicMock:
    """Create a mock I18nContext."""
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(side_effect=lambda key, **_: f"[{key}]")
    return i18n


class TestGetVocabularyKeyboard:
    """Tests for get_vocabulary_keyboard function."""

    def test_keyboard_structure(self) -> None:
        """Creates basic vocabulary keyboard."""
        i18n = create_mock_i18n()

        keyboard = get_vocabulary_keyboard(i18n)

        assert len(keyboard.inline_keyboard) == ROWS_WITH_MENU
        # First row: Add words, Word lists
        assert keyboard.inline_keyboard[0][0].callback_data == "word:add"
        assert keyboard.inline_keyboard[0][1].callback_data == "lists:show"
        # Second row: Menu
        assert keyboard.inline_keyboard[1][0].callback_data == "menu:main"


class TestGetVocabularyPaginationKeyboard:
    """Tests for get_vocabulary_pagination_keyboard function."""

    def test_first_page_no_previous_button(self) -> None:
        """First page has no previous button."""
        i18n = create_mock_i18n()

        keyboard = get_vocabulary_pagination_keyboard(
            i18n,
            current_page=0,
            total_pages=TOTAL_PAGES_THREE,
        )

        # Find navigation row (second row)
        nav_row = keyboard.inline_keyboard[1]
        # Should have page indicator and next button
        assert len(nav_row) == NAV_BUTTONS_FIRST_PAGE
        assert nav_row[0].callback_data == "noop"  # Page indicator
        assert nav_row[1].callback_data == "vocab:page:1"  # Next

    def test_last_page_no_next_button(self) -> None:
        """Last page has no next button."""
        i18n = create_mock_i18n()

        keyboard = get_vocabulary_pagination_keyboard(
            i18n,
            current_page=2,
            total_pages=TOTAL_PAGES_THREE,
        )

        # Find navigation row
        nav_row = keyboard.inline_keyboard[1]
        # Should have prev button and page indicator
        assert len(nav_row) == NAV_BUTTONS_LAST_PAGE
        assert nav_row[0].callback_data == "vocab:page:1"  # Previous
        assert nav_row[1].callback_data == "noop"  # Page indicator

    def test_middle_page_both_buttons(self) -> None:
        """Middle page has both navigation buttons."""
        i18n = create_mock_i18n()

        keyboard = get_vocabulary_pagination_keyboard(
            i18n,
            current_page=1,
            total_pages=TOTAL_PAGES_THREE,
        )

        # Find navigation row
        nav_row = keyboard.inline_keyboard[1]
        # Should have prev, page indicator, and next
        assert len(nav_row) == NAV_BUTTONS_MIDDLE_PAGE
        assert nav_row[0].callback_data == "vocab:page:0"  # Previous
        assert nav_row[1].callback_data == "noop"  # Page indicator
        assert nav_row[2].callback_data == "vocab:page:2"  # Next

    def test_single_page_only_indicator(self) -> None:
        """Single page only shows page indicator."""
        i18n = create_mock_i18n()

        keyboard = get_vocabulary_pagination_keyboard(
            i18n,
            current_page=0,
            total_pages=TOTAL_PAGES_ONE,
        )

        # Find navigation row
        nav_row = keyboard.inline_keyboard[1]
        # Should only have page indicator
        assert len(nav_row) == NAV_BUTTONS_SINGLE_PAGE
        assert nav_row[0].callback_data == "noop"
        assert "1/1" in nav_row[0].text

    def test_filter_no_selection(self) -> None:
        """Filter shows 'all' as selected when no filter."""
        i18n = create_mock_i18n()

        keyboard = get_vocabulary_pagination_keyboard(
            i18n,
            current_page=0,
            total_pages=TOTAL_PAGES_ONE,
            current_filter=None,
        )

        # First row is filter row
        filter_row = keyboard.inline_keyboard[0]
        # All button should have checkmark
        assert "✓" in filter_row[0].text
        assert "✓" not in filter_row[1].text  # EN
        assert "✓" not in filter_row[2].text  # KO

    def test_filter_english_selected(self) -> None:
        """Filter shows English as selected."""
        i18n = create_mock_i18n()

        keyboard = get_vocabulary_pagination_keyboard(
            i18n,
            current_page=0,
            total_pages=TOTAL_PAGES_ONE,
            current_filter=Language.EN,
        )

        # First row is filter row
        filter_row = keyboard.inline_keyboard[0]
        assert "✓" not in filter_row[0].text  # All
        assert "✓" in filter_row[1].text  # EN
        assert "✓" not in filter_row[2].text  # KO

    def test_filter_korean_selected(self) -> None:
        """Filter shows Korean as selected."""
        i18n = create_mock_i18n()

        keyboard = get_vocabulary_pagination_keyboard(
            i18n,
            current_page=0,
            total_pages=TOTAL_PAGES_ONE,
            current_filter=Language.KO,
        )

        # First row is filter row
        filter_row = keyboard.inline_keyboard[0]
        assert "✓" not in filter_row[0].text  # All
        assert "✓" not in filter_row[1].text  # EN
        assert "✓" in filter_row[2].text  # KO

    def test_page_indicator_format(self) -> None:
        """Page indicator shows correct page numbers."""
        i18n = create_mock_i18n()

        keyboard = get_vocabulary_pagination_keyboard(
            i18n,
            current_page=2,
            total_pages=TOTAL_PAGES_FIVE,
        )

        # Find page indicator in navigation row
        nav_row = keyboard.inline_keyboard[1]
        page_indicator = next(btn for btn in nav_row if btn.callback_data == "noop")
        assert "3/5" in page_indicator.text

    def test_actions_row_present(self) -> None:
        """Actions row is always present."""
        i18n = create_mock_i18n()

        keyboard = get_vocabulary_pagination_keyboard(
            i18n,
            current_page=0,
            total_pages=TOTAL_PAGES_ONE,
        )

        # Last row should be actions
        actions_row = keyboard.inline_keyboard[-1]
        assert actions_row[0].callback_data == "word:add"
        assert actions_row[1].callback_data == "menu:main"
