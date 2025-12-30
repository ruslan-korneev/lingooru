"""Tests for start handler."""

from unittest.mock import AsyncMock, MagicMock, patch

from src.bot.handlers.start import (
    cmd_start,
    on_language_selected,
    on_pair_selected,
)
from src.modules.users.dto import UserReadDTO


class TestCmdStart:
    """Tests for cmd_start handler."""

    async def test_sends_welcome_message(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
    ) -> None:
        """Handler sends welcome message with language selection."""
        await cmd_start(mock_message, mock_i18n)

        mock_message.answer.assert_called_once()
        mock_i18n.get.assert_any_call("welcome")
        mock_i18n.get.assert_any_call("welcome-choose-lang")


class TestOnLanguageSelected:
    """Tests for on_language_selected handler."""

    async def test_returns_early_when_no_data(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when callback has no data."""
        mock_callback.data = None

        await on_language_selected(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.data = "settings:lang:en"
        mock_callback.message = None

        await on_language_selected(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.data = "settings:lang:en"
        mock_callback.message = MagicMock()  # Not a Message instance

        await on_language_selected(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_updates_language_and_shows_pair_selection(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler updates language and shows pair selection."""
        mock_callback.data = "settings:lang:en"
        mock_callback.message = mock_message

        with patch("src.bot.handlers.start.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.start.UserService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.update = AsyncMock()

                await on_language_selected(mock_callback, mock_i18n, db_user)

        mock_service.update.assert_called_once()
        mock_i18n.set_locale.assert_called_with("en")
        mock_message.edit_text.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnPairSelected:
    """Tests for on_pair_selected handler."""

    async def test_returns_early_when_no_data(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when callback has no data."""
        mock_callback.data = None

        await on_pair_selected(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.data = "settings:pair:en_ru"
        mock_callback.message = None

        await on_pair_selected(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.data = "settings:pair:en_ru"
        mock_callback.message = MagicMock()  # Not a Message instance

        await on_pair_selected(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_updates_pair_and_shows_main_menu(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler updates language pair and shows main menu."""
        mock_callback.data = "settings:pair:en_ru"
        mock_callback.message = mock_message

        with patch("src.bot.handlers.start.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.start.UserService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.update = AsyncMock(return_value=db_user)

                with patch("src.bot.handlers.start._build_menu_text", new_callable=AsyncMock) as mock_build:
                    mock_build.return_value = "Menu text"

                    await on_pair_selected(mock_callback, mock_i18n, db_user)

        mock_service.update.assert_called_once()
        mock_message.edit_text.assert_called_once()
        mock_callback.answer.assert_called_once()
