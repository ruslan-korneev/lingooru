from uuid import UUID

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_i18n import I18nContext
from sqlalchemy.exc import SQLAlchemyError

from src.bot.keyboards.learn import (
    get_learning_card_keyboard,
    get_learning_complete_keyboard,
    get_word_added_keyboard,
    get_word_not_found_keyboard,
)
from src.bot.utils import get_flag, get_language_pair, parse_callback_param, safe_edit_or_send
from src.core.exceptions import ConflictError
from src.db.session import AsyncSessionMaker
from src.modules.srs.services import SRSService
from src.modules.users.dto import UserReadDTO
from src.modules.vocabulary.models import Language
from src.modules.vocabulary.services import VocabularyService

router = Router(name="learn")


class LearnStates(StatesGroup):
    waiting_for_translation = State()
    learning_session = State()


@router.callback_query(F.data == "learn:start")
async def on_learn_start(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
    state: FSMContext,
) -> None:
    """Start learning session with user's current language pair."""
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    # Get user's current language pair
    source_lang, _ = get_language_pair(db_user.language_pair)

    async with AsyncSessionMaker() as session:
        service = VocabularyService(session)
        unlearned_count = await service.count_unlearned_for_language(db_user.id, source_lang)

    if unlearned_count == 0:
        # No words for current language pair - redirect to add words
        await safe_edit_or_send(
            message,
            text=i18n.get("learn-no-words-for-pair"),
            reply_markup=get_word_not_found_keyboard(i18n),
        )
        await callback.answer()
        return

    # Start learning session directly with current language pair
    await _start_learning_session(
        message=message,
        i18n=i18n,
        db_user=db_user,
        state=state,
        source_language=source_lang,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("learn:lang:"))
async def on_learn_language_selected(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
    state: FSMContext,
) -> None:
    """Handle language selection for learning."""
    if not callback.data or not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    lang_code = parse_callback_param(callback.data, 2)  # "en", "ko", or "mix"

    source_language: Language | None = None
    if lang_code == "en":
        source_language = Language.EN
    elif lang_code == "ko":
        source_language = Language.KO
    # "mix" keeps source_language as None (all languages)

    await _start_learning_session(
        message=message,
        i18n=i18n,
        db_user=db_user,
        state=state,
        source_language=source_language,
    )
    await callback.answer()


async def _start_learning_session(
    message: Message,
    i18n: I18nContext,
    db_user: UserReadDTO,
    state: FSMContext,
    source_language: Language | None,
) -> None:
    """Start learning session with given source language filter."""
    _, target_lang = get_language_pair(db_user.language_pair)

    async with AsyncSessionMaker() as session:
        service = VocabularyService(session)
        words = await service.get_words_for_learning(
            user_id=db_user.id,
            target_language=target_lang,
            source_language=source_language,
            limit=20,
        )

    if not words:
        await safe_edit_or_send(
            message,
            text=i18n.get("learn-no-words"),
            reply_markup=get_word_not_found_keyboard(i18n),
        )
        return

    # Store learning session data
    await state.update_data(
        learning_words=[w.model_dump(mode="json") for w in words],
        current_index=0,
        total_words=len(words),
        source_language=source_language.value if source_language else None,
    )
    await state.set_state(LearnStates.learning_session)

    # Show first word with flag
    word = words[0]
    flag = get_flag(word.word.language)
    phonetic_text = f"\n{word.word.phonetic}" if word.word.phonetic else ""
    example_text = f'\n\n"{word.word.example_sentence}"' if word.word.example_sentence else ""

    text = i18n.get(
        "learn-card",
        position=1,
        total=len(words),
        word=f"{flag} {word.word.text}",
        phonetic=phonetic_text,
        translation=word.word.translation,
        example=example_text,
    )

    await safe_edit_or_send(
        message,
        text=text,
        reply_markup=get_learning_card_keyboard(i18n, word_id=word.word.id),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(
    F.data.in_({"learn:know", "learn:hard", "learn:forgot", "learn:skip"}),
    LearnStates.learning_session,
)
async def on_learn_action(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
    state: FSMContext,
) -> None:
    """Handle learning actions: know/hard/forgot/skip."""
    if not callback.data or not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    action = parse_callback_param(callback.data, 1)
    data = await state.get_data()
    words = data.get("learning_words", [])
    current_index = data.get("current_index", 0)

    if not words:
        await state.clear()
        await callback.answer(i18n.get("learn-session-ended"), show_alert=True)
        return

    current_word = words[current_index]
    _, target_lang = get_language_pair(db_user.language_pair)

    # Handle action
    if action == "know":
        # Mark as learned and create Review for SM-2 tracking
        async with AsyncSessionMaker() as session:
            vocab_service = VocabularyService(session)
            await vocab_service.mark_word_learned(current_word["id"])

            # Create Review entry for spaced repetition
            srs_service = SRSService(session)
            await srs_service.get_or_create_review(current_word["id"])

            await session.commit()
    # hard, forgot, skip - just move to next

    # Move to next word
    next_index = current_index + 1

    if next_index >= len(words):
        # Session complete
        await state.clear()
        await safe_edit_or_send(
            message,
            text=i18n.get("learn-session-complete", count=len(words)),
            reply_markup=get_learning_complete_keyboard(i18n),
        )
        await callback.answer(i18n.get("learn-session-ended"))
        return

    await state.update_data(current_index=next_index)

    # Show next word with flag
    next_word_data = words[next_index]
    word_data = next_word_data["word"]
    word_lang = Language(word_data["language"])
    flag = get_flag(word_lang)
    phonetic_text = f"\n{word_data['phonetic']}" if word_data.get("phonetic") else ""
    example_text = f'\n\n"{word_data["example_sentence"]}"' if word_data.get("example_sentence") else ""

    text = i18n.get(
        "learn-card",
        position=next_index + 1,
        total=len(words),
        word=f"{flag} {word_data['text']}",
        phonetic=phonetic_text,
        translation=word_data["translation"],
        example=example_text,
    )

    word_id = UUID(word_data["id"])

    await safe_edit_or_send(
        message,
        text=text,
        reply_markup=get_learning_card_keyboard(i18n, word_id=word_id),
        parse_mode=ParseMode.HTML,
    )
    await callback.answer()


@router.callback_query(F.data == "word:add")
async def on_word_add_prompt(
    callback: CallbackQuery,
    i18n: I18nContext,
) -> None:
    """Prompt user to add a word."""
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    await safe_edit_or_send(
        message,
        text=i18n.get("word-add-prompt"),
    )
    await callback.answer()


@router.message(LearnStates.waiting_for_translation)
async def on_translation_input(
    message: Message,
    i18n: I18nContext,
    db_user: UserReadDTO,
    state: FSMContext,
) -> None:
    """Handle manual translation input."""
    data = await state.get_data()
    pending_word = data.get("pending_word")

    if not pending_word or not message.text:
        await state.clear()
        return

    translation = message.text.strip()
    source_lang, target_lang = get_language_pair(db_user.language_pair)

    async with AsyncSessionMaker() as session:
        service = VocabularyService(session)
        try:
            user_word = await service.add_word_with_translation(
                user_id=db_user.id,
                text=pending_word,
                translation=translation,
                source_language=source_lang,
                target_language=target_lang,
            )
            await session.commit()

            await state.clear()

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
            await state.clear()
            await message.answer(text=i18n.get("word-already-exists"))
        except SQLAlchemyError:
            await state.clear()
            await message.answer(text=i18n.get("word-add-error"))
