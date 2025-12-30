"""Tests for menu handler."""

from unittest.mock import AsyncMock, MagicMock, patch

from src.bot.handlers.menu import (
    _build_menu_text,
    on_add_words,
    on_change_language,
    on_change_pair,
    on_coming_soon,
    on_main_menu,
    on_settings,
)
from src.modules.users.dto import UserReadDTO
from src.modules.vocabulary.enums import Language


class TestOnMainMenu:
    """Tests for on_main_menu handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await on_main_menu(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.message = MagicMock()  # Not a Message instance

        await on_main_menu(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_shows_main_menu(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows main menu with stats."""
        mock_callback.message = mock_message

        with patch("src.bot.handlers.menu._build_menu_text", new_callable=AsyncMock) as mock_build:
            mock_build.return_value = "Menu text"

            with patch("src.bot.handlers.menu.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit:
                await on_main_menu(mock_callback, mock_i18n, db_user)

        mock_build.assert_called_once_with(mock_i18n, db_user)
        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestBuildMenuText:
    """Tests for _build_menu_text helper."""

    async def test_builds_text_with_stats(
        self,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Builds menu text with vocabulary stats."""
        with patch("src.bot.handlers.menu.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.menu.VocabularyService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_stats_by_language = AsyncMock(return_value={Language.EN: (5, 10)})

                result = await _build_menu_text(mock_i18n, db_user)

        assert isinstance(result, str)
        mock_i18n.get.assert_any_call("menu-title")

    async def test_builds_text_without_stats(
        self,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Builds menu text when no vocabulary stats."""
        with patch("src.bot.handlers.menu.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.menu.VocabularyService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_stats_by_language = AsyncMock(return_value={})

                result = await _build_menu_text(mock_i18n, db_user)

        assert isinstance(result, str)


class TestOnSettings:
    """Tests for on_settings handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await on_settings(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.message = MagicMock()

        await on_settings(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_shows_settings(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows settings screen."""
        mock_callback.message = mock_message

        with patch("src.bot.handlers.menu.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit:
            await on_settings(mock_callback, mock_i18n, db_user)

        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnChangeLanguage:
    """Tests for on_change_language handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await on_change_language(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.message = MagicMock()

        await on_change_language(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_shows_language_selection(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows language selection screen."""
        mock_callback.message = mock_message

        with patch("src.bot.handlers.menu.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit:
            await on_change_language(mock_callback, mock_i18n, db_user)

        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnChangePair:
    """Tests for on_change_pair handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await on_change_pair(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.message = MagicMock()

        await on_change_pair(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_shows_pair_selection(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows pair selection screen."""
        mock_callback.message = mock_message

        with patch("src.bot.handlers.menu.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit:
            await on_change_pair(mock_callback, mock_i18n, db_user)

        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnAddWords:
    """Tests for on_add_words handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await on_add_words(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.message = MagicMock()

        await on_add_words(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_shows_empty_message_when_no_lists(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows empty message when no word lists available."""
        mock_callback.message = mock_message

        with (
            patch("src.bot.handlers.menu.get_word_lists_by_language", return_value=[]),
            patch("src.bot.handlers.menu.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit,
        ):
            await on_add_words(mock_callback, mock_i18n, db_user)

        mock_i18n.get.assert_any_call("lists-empty")
        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()

    async def test_shows_word_lists(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows word lists keyboard."""
        mock_callback.message = mock_message

        mock_word_list = MagicMock()
        mock_word_list.id = "test_list"
        mock_word_list.get_name = MagicMock(return_value="Test List")

        with (
            patch("src.bot.handlers.menu.get_word_lists_by_language", return_value=[mock_word_list]),
            patch("src.bot.handlers.menu.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit,
        ):
            await on_add_words(mock_callback, mock_i18n, db_user)

        mock_i18n.get.assert_any_call("lists-title")
        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnComingSoon:
    """Tests for on_coming_soon handler."""

    async def test_shows_coming_soon_alert(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler shows coming soon alert."""
        await on_coming_soon(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_called_once()
        mock_i18n.get.assert_any_call("coming-soon")
