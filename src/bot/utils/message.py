"""Message utilities for Telegram bot handlers."""

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, Message


async def safe_edit_or_send(
    message: Message,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    parse_mode: str | None = None,
) -> None:
    """Edit message text, or delete and send new if message is audio/media.

    Telegram doesn't allow editing audio/media messages to text messages.
    This function handles that by deleting the original and sending a new one.

    Args:
        message: The message to edit or replace.
        text: The new text content.
        reply_markup: Optional inline keyboard markup.
        parse_mode: Optional parse mode (HTML, Markdown, etc.).
    """
    try:
        await message.edit_text(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    except TelegramBadRequest as e:
        if "no text in the message" in str(e):
            await message.delete()
            await message.answer(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            raise
