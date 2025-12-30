"""Tests for message utilities."""

from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods.base import TelegramMethod

from src.bot.utils.message import safe_edit_or_send


class TestSafeEditOrSend:
    """Tests for safe_edit_or_send function."""

    async def test_edits_text_successfully(self) -> None:
        """Function edits text when edit_text succeeds."""
        message = MagicMock()
        message.edit_text = AsyncMock()

        await safe_edit_or_send(
            message,
            text="New text",
            reply_markup=None,
            parse_mode="HTML",
        )

        message.edit_text.assert_called_once_with(
            text="New text",
            reply_markup=None,
            parse_mode="HTML",
        )

    async def test_deletes_and_answers_when_no_text_in_message(self) -> None:
        """Function deletes and sends new message when original has no text."""
        message = MagicMock()
        message.edit_text = AsyncMock(
            side_effect=TelegramBadRequest(
                method=cast(TelegramMethod, "editMessageText"),  # type: ignore[type-arg]
                message="Bad Request: there is no text in the message to edit",
            )
        )
        message.delete = AsyncMock()
        message.answer = AsyncMock()

        keyboard = MagicMock()

        await safe_edit_or_send(
            message,
            text="New text",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

        message.delete.assert_called_once()
        message.answer.assert_called_once_with(
            text="New text",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

    async def test_reraises_other_telegram_errors(self) -> None:
        """Function reraises TelegramBadRequest for other errors."""
        message = MagicMock()
        message.edit_text = AsyncMock(
            side_effect=TelegramBadRequest(
                method=cast(TelegramMethod, "editMessageText"),  # type: ignore[type-arg]
                message="Bad Request: message is not modified",
            )
        )

        with pytest.raises(TelegramBadRequest) as exc_info:
            await safe_edit_or_send(
                message,
                text="Same text",
            )

        assert "message is not modified" in str(exc_info.value)

    async def test_works_with_default_parameters(self) -> None:
        """Function works with default optional parameters."""
        message = MagicMock()
        message.edit_text = AsyncMock()

        await safe_edit_or_send(message, text="Text only")

        message.edit_text.assert_called_once_with(
            text="Text only",
            reply_markup=None,
            parse_mode=None,
        )
