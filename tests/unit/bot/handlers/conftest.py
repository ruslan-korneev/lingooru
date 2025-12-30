"""Fixtures for bot handler tests."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Chat, Message, User
from aiogram_i18n import I18nContext

from src.modules.users.dto import UserReadDTO
from src.modules.users.models import LanguagePair, UILanguage


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
