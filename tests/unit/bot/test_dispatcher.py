"""Tests for bot dispatcher."""

from unittest.mock import MagicMock, patch

from src.bot.dispatcher import (
    _BotHolder,
    create_bot,
    create_dispatcher,
    get_bot,
    get_dispatcher,
)


class TestCreateBot:
    """Tests for create_bot function."""

    def test_creates_bot_with_token(self) -> None:
        """Creates bot with token from settings."""
        with (
            patch("src.bot.dispatcher.settings") as mock_settings,
            patch("src.bot.dispatcher.Bot") as mock_bot_class,
        ):
            mock_settings.telegram.bot_token.get_secret_value.return_value = "123456:ABC-DEF"
            mock_bot = MagicMock()
            mock_bot_class.return_value = mock_bot

            result = create_bot()

            mock_bot_class.assert_called_once()
            assert result == mock_bot


class TestCreateDispatcher:
    """Tests for create_dispatcher function."""

    def test_creates_dispatcher_with_routers(self) -> None:
        """Creates dispatcher with all routers included."""
        with (
            patch("src.bot.dispatcher.settings") as mock_settings,
            patch("src.bot.dispatcher.FluentRuntimeCore"),
            patch("src.bot.dispatcher.I18nMiddleware") as mock_i18n_middleware,
        ):
            mock_settings.telegram.bot_token.get_secret_value.return_value = "test-token"
            mock_i18n_middleware.return_value.setup = MagicMock()

            dp = create_dispatcher()

            # Verify dispatcher was created
            assert dp is not None
            # Verify i18n middleware was set up
            mock_i18n_middleware.return_value.setup.assert_called_once()


class TestBotHolder:
    """Tests for _BotHolder singleton."""

    def setup_method(self) -> None:
        """Reset singleton before each test."""
        _BotHolder._bot = None  # noqa: SLF001
        _BotHolder._dispatcher = None  # noqa: SLF001
        _BotHolder._i18n_middleware = None  # noqa: SLF001

    def test_get_bot_creates_bot_on_first_call(self) -> None:
        """get_bot creates bot on first call."""
        with patch("src.bot.dispatcher.create_bot") as mock_create:
            mock_bot = MagicMock()
            mock_create.return_value = mock_bot

            result = _BotHolder.get_bot()

            mock_create.assert_called_once()
            assert result == mock_bot

    def test_get_bot_returns_cached_bot(self) -> None:
        """get_bot returns cached bot on subsequent calls."""
        with patch("src.bot.dispatcher.create_bot") as mock_create:
            mock_bot = MagicMock()
            mock_create.return_value = mock_bot

            result1 = _BotHolder.get_bot()
            result2 = _BotHolder.get_bot()

            # create_bot should only be called once
            mock_create.assert_called_once()
            assert result1 == result2 == mock_bot

    def test_get_dispatcher_creates_dispatcher_on_first_call(self) -> None:
        """get_dispatcher creates dispatcher on first call."""
        with patch("src.bot.dispatcher.create_dispatcher") as mock_create:
            mock_dp = MagicMock()
            mock_i18n = MagicMock()
            mock_create.return_value = (mock_dp, mock_i18n)

            result = _BotHolder.get_dispatcher()

            mock_create.assert_called_once()
            assert result == mock_dp

    def test_get_dispatcher_returns_cached_dispatcher(self) -> None:
        """get_dispatcher returns cached dispatcher on subsequent calls."""
        with patch("src.bot.dispatcher.create_dispatcher") as mock_create:
            mock_dp = MagicMock()
            mock_i18n = MagicMock()
            mock_create.return_value = (mock_dp, mock_i18n)

            result1 = _BotHolder.get_dispatcher()
            result2 = _BotHolder.get_dispatcher()

            # create_dispatcher should only be called once
            mock_create.assert_called_once()
            assert result1 == result2 == mock_dp


class TestModuleFunctions:
    """Tests for module-level get_bot and get_dispatcher functions."""

    def setup_method(self) -> None:
        """Reset singleton before each test."""
        _BotHolder._bot = None  # noqa: SLF001
        _BotHolder._dispatcher = None  # noqa: SLF001
        _BotHolder._i18n_middleware = None  # noqa: SLF001

    def test_get_bot_uses_holder(self) -> None:
        """get_bot uses _BotHolder."""
        with patch.object(_BotHolder, "get_bot") as mock_get:
            mock_bot = MagicMock()
            mock_get.return_value = mock_bot

            result = get_bot()

            mock_get.assert_called_once()
            assert result == mock_bot

    def test_get_dispatcher_uses_holder(self) -> None:
        """get_dispatcher uses _BotHolder."""
        with patch.object(_BotHolder, "get_dispatcher") as mock_get:
            mock_dp = MagicMock()
            mock_get.return_value = mock_dp

            result = get_dispatcher()

            mock_get.assert_called_once()
            assert result == mock_dp
