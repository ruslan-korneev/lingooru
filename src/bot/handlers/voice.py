"""Voice handler for pronunciation practice sessions."""

from datetime import UTC, datetime
from io import BytesIO
from uuid import UUID

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_i18n import I18nContext
from httpx import HTTPError
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError

from src.bot.keyboards.voice import (
    get_voice_complete_keyboard,
    get_voice_no_words_keyboard,
    get_voice_prompt_keyboard,
    get_voice_result_keyboard,
)
from src.bot.utils import get_flag, get_language_pair, safe_edit_or_send
from src.db.session import AsyncSessionMaker
from src.modules.users.dto import UserReadDTO
from src.modules.vocabulary.models import Language
from src.modules.voice.services import VoiceService

router = Router(name="voice")


class VoiceStates(StatesGroup):
    """FSM states for pronunciation practice."""

    waiting_for_voice = State()  # Show word, wait for voice message
    processing = State()  # Processing voice message
    showing_result = State()  # Show result with feedback


@router.callback_query(F.data == "voice:start")
async def on_voice_start(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
    state: FSMContext,
) -> None:
    """Start pronunciation practice session."""
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    await state.clear()

    source_lang, _ = get_language_pair(db_user.language_pair)

    async with AsyncSessionMaker() as session:
        service = VoiceService(session)
        words = await service.get_words_for_pronunciation(
            user_id=db_user.id,
            source_language=source_lang,
            limit=10,
        )

    if not words:
        await safe_edit_or_send(
            message,
            text=i18n.get("voice-no-words"),
            reply_markup=get_voice_no_words_keyboard(i18n),
        )
        await callback.answer()
        return

    # Initialize session
    await state.update_data(
        words=[w.model_dump(mode="json") for w in words],
        current_index=0,
        session_start=datetime.now(tz=UTC).isoformat(),
        log_ids=[],
    )
    await state.set_state(VoiceStates.waiting_for_voice)

    # Show first word
    word = words[0]
    await _show_word_prompt(message, i18n, word.text, word.phonetic, word.language, 1, len(words), word_id=word.id)
    await callback.answer()


async def _show_word_prompt(
    message: Message,
    i18n: I18nContext,
    word_text: str,
    phonetic: str | None,
    language: str,
    position: int,
    total: int,
    word_id: UUID | None = None,
) -> None:
    """Show word pronunciation prompt."""
    flag = get_flag(Language(language))
    phonetic_text = f"\n{phonetic}" if phonetic else ""

    text = i18n.get(
        "voice-prompt",
        position=position,
        total=total,
        word=f"{flag} {word_text}",
        phonetic=phonetic_text,
    )

    await safe_edit_or_send(
        message,
        text=text,
        reply_markup=get_voice_prompt_keyboard(i18n, word_id=word_id),
        parse_mode=ParseMode.HTML,
    )


@router.message(F.voice, VoiceStates.waiting_for_voice)
async def on_voice_message(
    message: Message,
    i18n: I18nContext,
    db_user: UserReadDTO,
    state: FSMContext,
) -> None:
    """Handle voice message for pronunciation check."""
    if not message.voice or not message.bot:
        return

    data = await state.get_data()
    words = data.get("words", [])
    current_index = data.get("current_index", 0)
    log_ids = data.get("log_ids", [])

    if not words or current_index >= len(words):
        await state.clear()
        return

    current_word = words[current_index]
    await state.set_state(VoiceStates.processing)

    # Show processing message
    processing_msg = await message.answer(
        text=i18n.get("voice-processing"),
    )

    try:
        # Download voice file from Telegram
        file = await message.bot.get_file(message.voice.file_id)
        if not file.file_path:
            await state.set_state(VoiceStates.waiting_for_voice)
            await processing_msg.edit_text(
                text=i18n.get("voice-error"),
                reply_markup=get_voice_prompt_keyboard(i18n),
            )
            return

        file_data = await message.bot.download_file(file.file_path)
        if not isinstance(file_data, BytesIO):
            await state.set_state(VoiceStates.waiting_for_voice)
            await processing_msg.edit_text(
                text=i18n.get("voice-error"),
                reply_markup=get_voice_prompt_keyboard(i18n),
            )
            return
        audio_bytes = file_data.read()

        # Process pronunciation
        async with AsyncSessionMaker() as session:
            service = VoiceService(session)
            log = await service.process_voice_message(
                user_id=db_user.id,
                word_id=UUID(current_word["id"]),
                expected_text=current_word["text"],
                audio_bytes=audio_bytes,
                language=current_word["language"],
                phonetic=current_word.get("phonetic"),
            )
            await session.commit()

        log_ids.append(str(log.id))
        await state.update_data(log_ids=log_ids)
        await state.set_state(VoiceStates.showing_result)

        # Build rating display
        rating_stars = "\u2b50" * log.rating + "\u2606" * (5 - log.rating)

        text = i18n.get(
            "voice-result",
            transcribed=log.transcribed_text or "-",
            expected=current_word.get("phonetic") or current_word["text"],
            rating=rating_stars,
            rating_num=log.rating,
            feedback=log.feedback,
        )

        await processing_msg.edit_text(
            text=text,
            reply_markup=get_voice_result_keyboard(i18n),
            parse_mode=ParseMode.HTML,
        )

    except (TelegramBadRequest, HTTPError, SQLAlchemyError) as e:
        logger.error(f"Voice processing error: {e}")
        await state.set_state(VoiceStates.waiting_for_voice)
        await processing_msg.edit_text(
            text=i18n.get("voice-error"),
            reply_markup=get_voice_prompt_keyboard(i18n),
        )


@router.callback_query(F.data == "voice:retry", VoiceStates.showing_result)
async def on_voice_retry(
    callback: CallbackQuery,
    i18n: I18nContext,
    state: FSMContext,
) -> None:
    """Retry pronunciation of current word."""
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    data = await state.get_data()
    words = data.get("words", [])
    current_index = data.get("current_index", 0)

    if not words or current_index >= len(words):
        await state.clear()
        await callback.answer()
        return

    current_word = words[current_index]
    await state.set_state(VoiceStates.waiting_for_voice)

    await _show_word_prompt(
        message,
        i18n,
        current_word["text"],
        current_word.get("phonetic"),
        current_word["language"],
        current_index + 1,
        len(words),
        word_id=UUID(current_word["id"]),
    )
    await callback.answer()


@router.callback_query(F.data.in_({"voice:next", "voice:skip"}))
async def on_voice_next(
    callback: CallbackQuery,
    i18n: I18nContext,
    state: FSMContext,
) -> None:
    """Move to next word or complete session."""
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    data = await state.get_data()
    words = data.get("words", [])
    current_index = data.get("current_index", 0)
    log_ids = data.get("log_ids", [])

    next_index = current_index + 1

    if next_index >= len(words):
        # Session complete
        session_start = datetime.fromisoformat(data.get("session_start", datetime.now(tz=UTC).isoformat()))

        if log_ids:
            async with AsyncSessionMaker() as session:
                service = VoiceService(session)
                stats = await service.get_session_stats(
                    log_ids=[UUID(lid) for lid in log_ids],
                    session_start=session_start,
                )

            time_minutes = max(1, stats.time_spent_seconds // 60)

            await state.clear()
            await safe_edit_or_send(
                message,
                text=i18n.get(
                    "voice-complete",
                    count=stats.total_practiced,
                    avg_rating=stats.average_rating,
                    time=time_minutes,
                ),
                reply_markup=get_voice_complete_keyboard(i18n),
            )
        else:
            await state.clear()
            await safe_edit_or_send(
                message,
                text=i18n.get("voice-session-ended"),
                reply_markup=get_voice_complete_keyboard(i18n),
            )

        await callback.answer(i18n.get("voice-session-ended"))
        return

    # Update state and show next word
    await state.update_data(current_index=next_index)
    await state.set_state(VoiceStates.waiting_for_voice)

    next_word = words[next_index]
    await _show_word_prompt(
        message,
        i18n,
        next_word["text"],
        next_word.get("phonetic"),
        next_word["language"],
        next_index + 1,
        len(words),
        word_id=UUID(next_word["id"]),
    )
    await callback.answer()
