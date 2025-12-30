from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram_i18n import I18nContext

from src.bot.keyboards.menu import get_main_menu_keyboard
from src.bot.keyboards.word_lists import (
    get_list_added_keyboard,
    get_word_list_preview_keyboard,
    get_word_lists_keyboard,
)
from src.bot.utils import get_language_pair, parse_callback_param
from src.core.exceptions import ConflictError
from src.db.session import AsyncSessionMaker
from src.modules.users.dto import UserReadDTO
from src.modules.vocabulary.services import VocabularyService
from src.modules.vocabulary.word_lists import (
    get_word_list_by_id,
    get_word_lists_by_language,
)

router = Router(name="word_lists")

PREVIEW_WORD_COUNT = 5


@router.callback_query(F.data == "lists:show")
async def on_lists_show(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Show available word lists for user's learning language."""
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    # Filter lists by user's source language
    source_lang, _ = get_language_pair(db_user.language_pair)
    word_lists = get_word_lists_by_language(source_lang)
    ui_lang = db_user.ui_language.value

    if not word_lists:
        await message.edit_text(
            text=i18n.get("lists-empty"),
            reply_markup=get_main_menu_keyboard(i18n),
        )
        await callback.answer()
        return

    # Get user's added lists
    async with AsyncSessionMaker() as session:
        service = VocabularyService(session)
        added_list_ids = await service.get_user_added_word_lists(db_user.id)

    await message.edit_text(
        text=i18n.get("lists-title"),
        reply_markup=get_word_lists_keyboard(i18n, word_lists, ui_lang, added_list_ids),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lists:preview:"))
async def on_list_preview(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Show preview of a word list."""
    if not callback.data or not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    list_id = parse_callback_param(callback.data, 2)
    word_list = get_word_list_by_id(list_id)

    if not list_id or not word_list:
        await callback.answer(i18n.get("list-not-found"), show_alert=True)
        return

    lang = db_user.ui_language.value

    # Check if list is already added
    async with AsyncSessionMaker() as session:
        service = VocabularyService(session)
        is_added = await service.is_word_list_added(db_user.id, list_id)

    # Build preview text
    lines = [
        word_list.get_name(lang),
        "",
        i18n.get("list-preview-words", count=len(word_list.words)),
        "",
    ]

    # Show preview words
    preview_lines = [f"• {item.text} — {item.translation}" for item in word_list.words[:PREVIEW_WORD_COUNT]]
    lines.extend(preview_lines)

    if len(word_list.words) > PREVIEW_WORD_COUNT:
        remaining = len(word_list.words) - PREVIEW_WORD_COUNT
        lines.append(f"... {i18n.get('list-and-more', count=remaining)}")

    await message.edit_text(
        text="\n".join(lines),
        reply_markup=get_word_list_preview_keyboard(i18n, list_id, is_added=is_added),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lists:add:"))
async def on_list_add(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Add words from a list to user's vocabulary."""
    if not callback.data or not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    list_id = parse_callback_param(callback.data, 2)
    word_list = get_word_list_by_id(list_id)

    if not list_id or not word_list:
        await callback.answer(i18n.get("list-not-found"), show_alert=True)
        return

    # Use list's source language, not user's setting
    source_lang = word_list.source_language
    _, target_lang = get_language_pair(db_user.language_pair)
    added_count = 0
    skipped_count = 0

    async with AsyncSessionMaker() as session:
        service = VocabularyService(session)

        # Check if list is already added
        if await service.is_word_list_added(db_user.id, list_id):
            await callback.answer(i18n.get("list-already-added"), show_alert=True)
            return

        for item in word_list.words:
            try:
                await service.add_word_with_translation(
                    user_id=db_user.id,
                    text=item.text,
                    translation=item.translation,
                    source_language=source_lang,
                    target_language=target_lang,
                    example_sentence=item.example,
                )
                added_count += 1
            except ConflictError:
                skipped_count += 1

        # Mark list as added
        await service.mark_word_list_added(db_user.id, list_id, added_count)

        await session.commit()

    lang = db_user.ui_language.value
    await message.edit_text(
        text=i18n.get(
            "list-added",
            list_name=word_list.get_name(lang),
            added=added_count,
            skipped=skipped_count,
        ),
        reply_markup=get_list_added_keyboard(i18n),
    )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def on_noop(callback: CallbackQuery, i18n: I18nContext) -> None:
    """Handle noop callback (disabled buttons)."""
    await callback.answer(i18n.get("list-already-added"))
