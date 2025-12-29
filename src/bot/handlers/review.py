"""Review handler for spaced repetition sessions."""

from datetime import UTC, datetime
from uuid import UUID

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram_i18n import I18nContext

from src.bot.handlers.learn import get_language_pair
from src.bot.keyboards.review import (
    get_review_complete_keyboard,
    get_review_rating_keyboard,
    get_review_show_answer_keyboard,
    get_review_start_keyboard,
)
from src.db.session import AsyncSessionMaker
from src.modules.srs.services import SRSService
from src.modules.users.dto import UserReadDTO

router = Router(name="review")


async def _safe_edit_or_send(
    message: Message,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    parse_mode: str | None = None,
) -> None:
    """Edit message text, or delete and send new if message is audio."""
    try:
        await message.edit_text(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    except TelegramBadRequest as e:
        if "no text in the message" in str(e):
            await message.delete()
            await message.answer(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            raise


class ReviewStates(StatesGroup):
    """FSM states for review session."""

    reviewing = State()  # showing question
    rating = State()  # showing answer + rating buttons


@router.callback_query(F.data == "review:start")
async def on_review_start(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
    state: FSMContext,
) -> None:
    """Show review start screen with due word count."""
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    # Clear any existing state
    await state.clear()

    async with AsyncSessionMaker() as session:
        service = SRSService(session)
        due_count = await service.count_due_reviews(db_user.id)

    if due_count == 0:
        await _safe_edit_or_send(
            message,
            text=i18n.get("review-no-words-due"),
            reply_markup=get_review_complete_keyboard(i18n),
        )
        await callback.answer()
        return

    await _safe_edit_or_send(
        message,
        text=i18n.get("review-start", count=due_count),
        reply_markup=get_review_start_keyboard(i18n),
    )
    await callback.answer()


@router.callback_query(F.data == "review:begin")
async def on_review_begin(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
    state: FSMContext,
) -> None:
    """Begin review session - load words and show first card."""
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    _, target_lang = get_language_pair(db_user.language_pair)

    async with AsyncSessionMaker() as session:
        service = SRSService(session)
        reviews = await service.get_due_reviews(
            user_id=db_user.id,
            target_language=target_lang,
            limit=20,
        )

    if not reviews:
        await _safe_edit_or_send(
            message,
            text=i18n.get("review-no-words-due"),
            reply_markup=get_review_complete_keyboard(i18n),
        )
        await callback.answer()
        return

    # Store session data
    await state.update_data(
        reviews=[r.model_dump(mode="json") for r in reviews],
        current_index=0,
        session_start=datetime.now(tz=UTC).isoformat(),
        reviewed_ids=[],
    )
    await state.set_state(ReviewStates.reviewing)

    # Show first question (translation prompt)
    review = reviews[0]
    await _safe_edit_or_send(
        message,
        text=i18n.get(
            "review-question",
            position=1,
            total=len(reviews),
            translation=review.translation,
        ),
        reply_markup=get_review_show_answer_keyboard(i18n),
    )
    await callback.answer()


@router.callback_query(F.data == "review:show", ReviewStates.reviewing)
async def on_review_show_answer(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,  # noqa: ARG001
    state: FSMContext,
) -> None:
    """Show the answer (word + phonetic) and rating buttons."""
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    data = await state.get_data()
    reviews = data.get("reviews", [])
    current_index = data.get("current_index", 0)

    if not reviews or current_index >= len(reviews):
        await state.clear()
        return

    review_data = reviews[current_index]
    await state.set_state(ReviewStates.rating)

    # Build answer text
    phonetic_text = f"\n{review_data['word_phonetic']}" if review_data.get("word_phonetic") else ""
    example_text = f'\n\n"{review_data["example_sentence"]}"' if review_data.get("example_sentence") else ""
    word_id = UUID(review_data["word_id"]) if review_data.get("word_id") else None

    await _safe_edit_or_send(
        message,
        text=i18n.get(
            "review-answer",
            position=current_index + 1,
            total=len(reviews),
            word=review_data["word_text"],
            phonetic=phonetic_text,
            example=example_text,
        ),
        reply_markup=get_review_rating_keyboard(i18n, word_id=word_id),
        parse_mode=ParseMode.HTML,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("review:rate:"), ReviewStates.rating)
async def on_review_rate(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,  # noqa: ARG001
    state: FSMContext,
) -> None:
    """Handle quality rating and move to next word."""
    if not callback.data or not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    quality = int(callback.data.split(":")[2])  # 1-5
    data = await state.get_data()
    reviews = data.get("reviews", [])
    current_index = data.get("current_index", 0)
    reviewed_ids = data.get("reviewed_ids", [])

    if not reviews or current_index >= len(reviews):
        await state.clear()
        return

    current_review = reviews[current_index]

    # Record the review
    async with AsyncSessionMaker() as session:
        service = SRSService(session)
        await service.record_review(
            review_id=current_review["id"],
            quality=quality,
        )
        await session.commit()

    reviewed_ids.append(current_review["id"])
    next_index = current_index + 1

    if next_index >= len(reviews):
        # Session complete
        session_start = datetime.fromisoformat(data.get("session_start", datetime.now(tz=UTC).isoformat()))

        async with AsyncSessionMaker() as session:
            service = SRSService(session)
            stats = await service.get_session_stats(reviewed_ids, session_start)

        await state.clear()

        # Calculate time in minutes
        time_minutes = max(1, stats.time_spent_seconds // 60)

        await _safe_edit_or_send(
            message,
            text=i18n.get(
                "review-complete",
                count=stats.total_reviewed,
                avg_rating=stats.average_quality,
                time=time_minutes,
            ),
            reply_markup=get_review_complete_keyboard(i18n),
        )
        await callback.answer(i18n.get("review-session-ended"))
        return

    # Update state and show next question
    await state.update_data(current_index=next_index, reviewed_ids=reviewed_ids)
    await state.set_state(ReviewStates.reviewing)

    next_review = reviews[next_index]
    await _safe_edit_or_send(
        message,
        text=i18n.get(
            "review-question",
            position=next_index + 1,
            total=len(reviews),
            translation=next_review["translation"],
        ),
        reply_markup=get_review_show_answer_keyboard(i18n),
    )
    await callback.answer()
