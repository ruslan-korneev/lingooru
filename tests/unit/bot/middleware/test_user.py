"""Tests for user middleware."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.types import CallbackQuery, Message, Update, User

from src.bot.middleware.user import UserMiddleware


class TestUserMiddleware:
    """Tests for UserMiddleware class."""

    async def test_extracts_user_from_message(self) -> None:
        """Middleware extracts user from Message event."""
        middleware = UserMiddleware()
        handler = AsyncMock()

        user = User(id=123, is_bot=False, first_name="Test", username="testuser")
        message = MagicMock(spec=Message)
        message.from_user = user

        data: dict[str, Any] = {}

        with (
            patch("src.bot.middleware.user.AsyncSessionMaker") as mock_session_maker,
            patch("src.bot.middleware.user.UserService") as mock_service_class,
        ):
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            mock_service = mock_service_class.return_value
            mock_user_dto = MagicMock()
            mock_service.get_or_create = AsyncMock(return_value=(mock_user_dto, False))

            await middleware(handler, message, data)

            mock_service.get_or_create.assert_called_once()
            assert data["db_user"] == mock_user_dto
            handler.assert_called_once()

    async def test_extracts_user_from_callback_query(self) -> None:
        """Middleware extracts user from CallbackQuery event."""
        middleware = UserMiddleware()
        handler = AsyncMock()

        user = User(id=456, is_bot=False, first_name="Callback", username="callbackuser")
        callback = MagicMock(spec=CallbackQuery)
        callback.from_user = user

        data: dict[str, Any] = {}

        with (
            patch("src.bot.middleware.user.AsyncSessionMaker") as mock_session_maker,
            patch("src.bot.middleware.user.UserService") as mock_service_class,
        ):
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            mock_service = mock_service_class.return_value
            mock_user_dto = MagicMock()
            mock_service.get_or_create = AsyncMock(return_value=(mock_user_dto, False))

            await middleware(handler, callback, data)

            mock_service.get_or_create.assert_called_once()
            assert data["db_user"] == mock_user_dto
            handler.assert_called_once()

    async def test_handles_message_without_from_user(self) -> None:
        """Middleware handles Message without from_user."""
        middleware = UserMiddleware()
        handler = AsyncMock()

        message = MagicMock(spec=Message)
        message.from_user = None

        data: dict[str, Any] = {}

        await middleware(handler, message, data)

        # Should still call handler but not set db_user
        handler.assert_called_once()
        assert "db_user" not in data

    async def test_handles_callback_without_from_user(self) -> None:
        """Middleware handles CallbackQuery without from_user."""
        middleware = UserMiddleware()
        handler = AsyncMock()

        callback = MagicMock(spec=CallbackQuery)
        callback.from_user = None

        data: dict[str, Any] = {}

        await middleware(handler, callback, data)

        # Should still call handler but not set db_user
        handler.assert_called_once()
        assert "db_user" not in data

    async def test_handles_other_event_types(self) -> None:
        """Middleware handles non-Message/CallbackQuery events."""
        middleware = UserMiddleware()
        handler = AsyncMock()

        # Create a generic TelegramObject (not Message or CallbackQuery)
        event = MagicMock(spec=Update)

        data: dict[str, Any] = {}

        await middleware(handler, event, data)

        # Should still call handler but not set db_user
        handler.assert_called_once()
        assert "db_user" not in data

    async def test_passes_correct_dto_to_service(self) -> None:
        """Middleware creates correct UserCreateDTO."""
        middleware = UserMiddleware()
        handler = AsyncMock()

        user = User(
            id=789,
            is_bot=False,
            first_name="TestFirst",
            username="testname",
        )
        message = MagicMock(spec=Message)
        message.from_user = user

        data: dict[str, Any] = {}

        with (
            patch("src.bot.middleware.user.AsyncSessionMaker") as mock_session_maker,
            patch("src.bot.middleware.user.UserService") as mock_service_class,
            patch("src.bot.middleware.user.UserCreateDTO") as mock_dto_class,
        ):
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            mock_service = mock_service_class.return_value
            mock_user_dto = MagicMock()
            mock_service.get_or_create = AsyncMock(return_value=(mock_user_dto, False))

            await middleware(handler, message, data)

            mock_dto_class.assert_called_once_with(
                telegram_id=789,
                username="testname",
                first_name="TestFirst",
            )

    async def test_commits_session_after_get_or_create(self) -> None:
        """Middleware commits session after user creation."""
        middleware = UserMiddleware()
        handler = AsyncMock()

        user = User(id=123, is_bot=False, first_name="Test")
        message = MagicMock(spec=Message)
        message.from_user = user

        data: dict[str, Any] = {}

        with (
            patch("src.bot.middleware.user.AsyncSessionMaker") as mock_session_maker,
            patch("src.bot.middleware.user.UserService") as mock_service_class,
        ):
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            mock_service = mock_service_class.return_value
            mock_user_dto = MagicMock()
            mock_service.get_or_create = AsyncMock(return_value=(mock_user_dto, False))

            await middleware(handler, message, data)

            mock_session.commit.assert_called_once()
