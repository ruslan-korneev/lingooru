from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram_i18n import I18nContext

from src.bot.constants import LEARN_BUTTONS, MENU_BUTTONS, REVIEW_BUTTONS
from src.bot.handlers.learn import LearnStates
from src.bot.keyboards.learn import get_word_added_keyboard
from src.bot.keyboards.vocabulary import (
    get_vocabulary_keyboard,
    get_vocabulary_pagination_keyboard,
)
from src.bot.utils import get_flag, get_language_pair, parse_callback_int, parse_callback_param
from src.core.exceptions import ConflictError
from src.db.session import AsyncSessionMaker
from src.modules.users.dto import UserReadDTO
from src.modules.vocabulary.models import Language
from src.modules.vocabulary.services import VocabularyService

router = Router(name="vocabulary")

ITEMS_PER_PAGE = 10
MAX_WORD_LENGTH = 100


@router.callback_query(F.data == "vocab:list")
async def on_vocab_list(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
    state: FSMContext,
) -> None:
    """Show user's vocabulary list."""
    # Reset filter when entering vocab list
    await state.update_data(vocab_filter=None)
    await show_vocabulary_page(callback, i18n, db_user, state, page=0)


@router.callback_query(F.data.startswith("vocab:page:"))
async def on_vocab_page(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
    state: FSMContext,
) -> None:
    """Navigate vocabulary pages."""
    if not callback.data:
        return

    page = parse_callback_int(callback.data, 2)
    await show_vocabulary_page(callback, i18n, db_user, state, page=page)


@router.callback_query(F.data.startswith("vocab:filter:"))
async def on_vocab_filter(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
    state: FSMContext,
) -> None:
    """Handle vocabulary language filter."""
    if not callback.data:
        return

    filter_code = parse_callback_param(callback.data, 2)  # "all", "en", "ko"

    source_filter: Language | None = None
    if filter_code == "en":
        source_filter = Language.EN
    elif filter_code == "ko":
        source_filter = Language.KO
    # "all" keeps source_filter as None

    await state.update_data(vocab_filter=source_filter.value if source_filter else None)
    await show_vocabulary_page(callback, i18n, db_user, state, page=0, source_filter=source_filter)


async def show_vocabulary_page(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
    state: FSMContext,
    page: int,
    source_filter: Language | None = None,
) -> None:
    """Show a page of user's vocabulary with optional language filter."""
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    # Get filter from state if not provided
    if source_filter is None:
        data = await state.get_data()
        filter_value = data.get("vocab_filter")
        if filter_value:
            source_filter = Language(filter_value)

    _, target_lang = get_language_pair(db_user.language_pair)
    offset = page * ITEMS_PER_PAGE

    async with AsyncSessionMaker() as session:
        service = VocabularyService(session)
        result = await service.get_user_vocabulary(
            user_id=db_user.id,
            target_language=target_lang,
            source_language=source_filter,
            limit=ITEMS_PER_PAGE,
            offset=offset,
        )

    if not result.items:
        await message.edit_text(
            text=i18n.get("vocab-empty"),
            reply_markup=get_vocabulary_keyboard(i18n),
        )
        await callback.answer()
        return

    # Build vocabulary list text with flags
    lines = [i18n.get("vocab-title", total=result.total), ""]
    for item in result.items:
        status = "✅" if item.is_learned else "📝"
        flag = get_flag(item.word.language)
        lines.append(f"{status} {flag} {item.word.text} — {item.word.translation}")

    total_pages = (result.total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    await message.edit_text(
        text="\n".join(lines),
        reply_markup=get_vocabulary_pagination_keyboard(
            i18n,
            current_page=page,
            total_pages=total_pages,
            current_filter=source_filter,
        ),
    )
    await callback.answer()


@router.message(F.text, ~F.text.startswith("/"))
async def on_text_input(
    message: Message,
    i18n: I18nContext,
    db_user: UserReadDTO,
    state: FSMContext,
) -> None:
    """Handle text input - could be a new word to add."""
    current_state = await state.get_state()

    # Skip if in learning session or waiting for translation
    if current_state in [
        LearnStates.learning_session.state,
        LearnStates.waiting_for_translation.state,
    ]:
        return

    text = message.text.strip() if message.text else ""
    if not text or len(text) > MAX_WORD_LENGTH:
        return

    # Skip if it's a menu button
    if text in MENU_BUTTONS | LEARN_BUTTONS | REVIEW_BUTTONS:
        return

    source_lang, target_lang = get_language_pair(db_user.language_pair)

    async with AsyncSessionMaker() as session:
        service = VocabularyService(session)

        # Try to look up the word in DB
        result = await service.lookup_word(text, source_lang, target_lang)

        if result:
            # Word found with translation - add to vocabulary
            try:
                user_word = await service.add_word_with_translation(
                    user_id=db_user.id,
                    text=result.text,
                    translation=result.translation,
                    source_language=source_lang,
                    target_language=target_lang,
                    example_sentence=result.example_sentence,
                    phonetic=result.phonetic,
                    audio_url=result.audio_url,
                )
                await session.commit()

                phonetic_text = f"\n{user_word.word.phonetic}" if user_word.word.phonetic else ""

                card_text = i18n.get(
                    "word-added",
                    word=user_word.word.text,
                    phonetic=phonetic_text,
                    translation=user_word.word.translation,
                )
                await message.answer(
                    text=card_text,
                    reply_markup=get_word_added_keyboard(i18n),
                )
            except ConflictError:
                await message.answer(text=i18n.get("word-already-exists"))
        else:
            # Word not found - ask for manual translation
            await state.update_data(pending_word=text)
            await state.set_state(LearnStates.waiting_for_translation)
            await message.answer(
                text=i18n.get("word-not-found-enter-translation", word=text),
            )


@router.callback_query(F.data == "noop")
async def on_noop(callback: CallbackQuery) -> None:
    """Handle noop callback (e.g., page indicator)."""
    await callback.answer()
