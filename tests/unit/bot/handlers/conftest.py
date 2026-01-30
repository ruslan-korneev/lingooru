"""Fixtures for bot handler tests."""

from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Chat, Message, User
from aiogram_i18n import I18nContext

from src.modules.users.dto import UserReadDTO
from src.modules.users.enums import LanguagePair, UILanguage

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def mock_user() -> User:
    """Create a mock Telegram User."""
    return User(
        id=123456789,
        is_bot=False,
        first_name="Test",
        username="testuser",
    )


@pytest.fixture
def mock_chat() -> Chat:
    """Create a mock Telegram Chat."""
    return Chat(id=123456789, type="private")


@pytest.fixture
def mock_message(mock_user: User, mock_chat: Chat) -> MagicMock:
    """Create a mock aiogram Message."""
    message = MagicMock(spec=Message)
    message.from_user = mock_user
    message.chat = mock_chat
    message.message_id = 1
    message.text = "test message"
    message.edit_text = AsyncMock()
    message.answer = AsyncMock()
    message.delete = AsyncMock()
    return message


@pytest.fixture
def mock_callback(mock_user: User, mock_message: MagicMock) -> MagicMock:
    """Create a mock aiogram CallbackQuery."""
    callback = MagicMock(spec=CallbackQuery)
    callback.id = "callback_123"
    callback.from_user = mock_user
    callback.data = "test:callback"
    callback.answer = AsyncMock()
    callback.message = mock_message
    return callback


@pytest.fixture
def mock_state() -> MagicMock:
    """Create a mock FSMContext."""
    state = MagicMock(spec=FSMContext)
    state.get_data = AsyncMock(return_value={})
    state.update_data = AsyncMock()
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    state.get_state = AsyncMock(return_value=None)
    return state


@pytest.fixture
def mock_i18n() -> MagicMock:
    """Create a mock I18nContext."""
    i18n = MagicMock(spec=I18nContext)

    def get_translation(key: str, **kwargs: Any) -> str:
        # Return a formatted string with key and params for testing
        if kwargs:
            params = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            return f"[{key}: {params}]"
        return f"[{key}]"

    i18n.get = MagicMock(side_effect=get_translation)
    return i18n


@pytest.fixture
def db_user() -> UserReadDTO:
    """Create a mock database user."""
    from datetime import UTC, datetime

    return UserReadDTO(
        id=uuid4(),
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        ui_language=UILanguage.RU,
        language_pair=LanguagePair.EN_RU,
        timezone="UTC",
        notifications_enabled=True,
        notification_times=["09:00", "21:00"],
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )


@pytest.fixture
def mock_user_service(db_user: UserReadDTO) -> MagicMock:
    """Create a mock UserService without patching.

    This fixture only creates the mock service object.
    For use with patched_user_service fixture.

    Usage:
        def test_something(mock_user_service):
            # mock_user_service.update is already an AsyncMock
            mock_user_service.update.return_value = some_user
    """
    mock_service = MagicMock()
    mock_service.update = AsyncMock(return_value=db_user)
    mock_service.get = AsyncMock(return_value=db_user)
    mock_service.get_by_telegram_id = AsyncMock(return_value=db_user)
    return mock_service


@pytest.fixture
def patched_start_user_service(
    mock_user_service: MagicMock,
) -> "Generator[MagicMock]":
    """Patch AsyncSessionMaker and UserService for start handler tests.

    This fixture patches both dependencies and yields the mock service
    for assertions in tests.

    Usage:
        async def test_something(patched_start_user_service, mock_callback, ...):
            patched_start_user_service.update.return_value = updated_user
            await on_language_selected(...)
            patched_start_user_service.update.assert_called_once()
    """
    from unittest.mock import patch

    with patch("src.bot.handlers.start.AsyncSessionMaker") as mock_session_maker:
        mock_session = AsyncMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_session

        with patch("src.bot.handlers.start.UserService") as mock_service_class:
            mock_service_class.return_value = mock_user_service
            yield mock_user_service
