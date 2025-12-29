"""Audio handler for playing word pronunciations."""

from uuid import UUID

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardMarkup, Message
from aiogram_i18n import I18nContext
from loguru import logger

from src.bot.keyboards.learn import get_learning_card_keyboard
from src.bot.keyboards.review import get_review_rating_keyboard
from src.bot.keyboards.voice import get_voice_prompt_keyboard
from src.db.session import AsyncSessionMaker
from src.modules.audio.services import AudioService
from src.modules.users.dto import UserReadDTO

router = Router(name="audio")


def _get_keyboard_for_context(
    context: str,
    i18n: I18nContext,
) -> InlineKeyboardMarkup | None:
    """Get keyboard for context without audio button."""
    if context == "learn":
        return get_learning_card_keyboard(i18n, word_id=None)
    if context == "review":
        return get_review_rating_keyboard(i18n, word_id=None)
    if context == "voice":
        return get_voice_prompt_keyboard(i18n, word_id=None)
    return None


@router.callback_query(F.data.startswith("audio:play:"))
async def on_audio_play(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,  # noqa: ARG001
) -> None:
    """Handle audio play request."""
    if not callback.data or not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    # Parse callback: audio:play:{context}:{word_id}
    expected_parts = 4
    parts = callback.data.split(":")
    if len(parts) != expected_parts:
        await callback.answer(i18n.get("audio-error"), show_alert=True)
        return

    context = parts[2]  # learn, review, voice

    try:
        word_id = UUID(parts[3])
    except ValueError:
        logger.error(f"Invalid word_id in callback: {callback.data}")
        await callback.answer(i18n.get("audio-error"), show_alert=True)
        return

    # Show loading indicator
    await callback.answer(i18n.get("audio-loading"))

    # Use original message text as caption (preserves exact formatting)
    caption = message.text or ""

    async with AsyncSessionMaker() as session:
        service = AudioService(session)
        audio_bytes = await service.get_audio_bytes(word_id)

        if not audio_bytes:
            await callback.answer(i18n.get("audio-not-available"), show_alert=True)
            return

        # Commit any changes (like audio_url update)
        await session.commit()

    keyboard = _get_keyboard_for_context(context, i18n)

    # Delete original message and send audio with caption + keyboard
    try:
        await message.delete()
        audio_file = BufferedInputFile(audio_bytes, filename="pronunciation.mp3")
        await message.answer_audio(audio_file, caption=caption, reply_markup=keyboard)
    except TelegramBadRequest as e:
        logger.error(f"Failed to send audio: {e}")
        await callback.answer(i18n.get("audio-error"), show_alert=True)
    except Exception as e:
        logger.error(f"Failed to send audio: {e}")
        await callback.answer(i18n.get("audio-error"), show_alert=True)
