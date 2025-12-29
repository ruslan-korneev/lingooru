"""Audio handler for playing word pronunciations."""

from uuid import UUID

from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from aiogram_i18n import I18nContext
from loguru import logger

from src.db.session import AsyncSessionMaker
from src.modules.audio.services import AudioService
from src.modules.users.dto import UserReadDTO

router = Router(name="audio")


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

    # Extract word_id from callback (format: "audio:play:{uuid}")
    expected_parts = 3
    parts = callback.data.split(":")
    if len(parts) != expected_parts:
        await callback.answer(i18n.get("audio-error"), show_alert=True)
        return

    try:
        word_id = UUID(parts[2])
    except ValueError:
        logger.error(f"Invalid word_id in callback: {callback.data}")
        await callback.answer(i18n.get("audio-error"), show_alert=True)
        return

    # Show loading indicator
    await callback.answer(i18n.get("audio-loading"))

    async with AsyncSessionMaker() as session:
        service = AudioService(session)
        audio_bytes = await service.get_audio_bytes(word_id)

        if not audio_bytes:
            await callback.answer(i18n.get("audio-not-available"), show_alert=True)
            return

        # Commit any changes (like audio_url update)
        await session.commit()

    # Send voice message
    try:
        voice_file = BufferedInputFile(audio_bytes, filename="pronunciation.mp3")
        await message.answer_voice(voice_file)
    except Exception as e:
        logger.error(f"Failed to send voice message: {e}")
        await callback.answer(i18n.get("audio-error"), show_alert=True)
