from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram_i18n import I18nContext
from loguru import logger

from src.bot.constants import PAIR_DISPLAY
from src.bot.keyboards.menu import (
    get_language_selection_keyboard,
    get_main_menu_keyboard,
    get_pair_selection_keyboard,
    get_settings_keyboard,
)
from src.bot.keyboards.word_lists import get_word_lists_keyboard
from src.bot.utils import get_flag, get_language_pair, safe_edit_or_send
from src.db.session import AsyncSessionMaker
from src.modules.users.dto import UserReadDTO
from src.modules.vocabulary.services import VocabularyService
from src.modules.vocabulary.word_lists import get_word_lists_by_language

router = Router(name="menu")


@router.callback_query(F.data == "menu:main")
async def on_main_menu(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    logger.debug(f"{__name__}:user:{db_user.username}")
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    text = await _build_menu_text(i18n, db_user)
    await safe_edit_or_send(
        message,
        text=text,
        reply_markup=get_main_menu_keyboard(i18n),
    )
    await callback.answer()


async def _build_menu_text(i18n: I18nContext, db_user: UserReadDTO) -> str:
    """Build menu text with stats per language."""
    async with AsyncSessionMaker() as session:
        service = VocabularyService(session)
        stats_by_lang = await service.get_stats_by_language(db_user.id)

    # Calculate totals
    total_learned = sum(learned for learned, _ in stats_by_lang.values())
    total_words = sum(total for _, total in stats_by_lang.values())

    pair_display = PAIR_DISPLAY.get(db_user.language_pair.value, db_user.language_pair.value)

    lines = [
        i18n.get("menu-title"),
        i18n.get("menu-subtitle"),
        f"📖 {pair_display}",
        "",
        i18n.get("menu-stats", learned=total_learned, total=total_words),
    ]

    # Add per-language breakdown if there are words
    if stats_by_lang:
        lang_stats = []
        for lang, (learned, total) in stats_by_lang.items():
            flag = get_flag(lang)
            lang_stats.append(i18n.get("menu-stats-by-lang", flag=flag, learned=learned, total=total))
        lines.append("  " + "  ".join(lang_stats))

    lines.append(i18n.get("menu-streak", days=0))

    return "\n".join(lines)


@router.callback_query(F.data == "settings:main")
async def on_settings(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    logger.debug(f"{__name__}:user:{db_user.username}")
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    lang_name = {
        "ru": "Русский",
        "en": "English",
        "ko": "한국어",
    }.get(db_user.ui_language.value, db_user.ui_language.value)

    pair_name = PAIR_DISPLAY.get(db_user.language_pair.value, db_user.language_pair.value)

    text = (
        f"{i18n.get('settings-title')}\n\n"
        f"{i18n.get('settings-lang', lang=lang_name)}\n"
        f"{i18n.get('settings-pair', pair=pair_name)}"
    )
    await safe_edit_or_send(
        message,
        text=text,
        reply_markup=get_settings_keyboard(i18n),
    )
    await callback.answer()


@router.callback_query(F.data == "settings:lang")
async def on_change_language(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    logger.debug(f"{__name__}:user:{db_user.username}")
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    await safe_edit_or_send(
        message,
        text=i18n.get("welcome-choose-lang"),
        reply_markup=get_language_selection_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "settings:pair")
async def on_change_pair(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    logger.debug(f"{__name__}:user:{db_user.username}")
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    await safe_edit_or_send(
        message,
        text=i18n.get("welcome-choose-pair"),
        reply_markup=get_pair_selection_keyboard(i18n),
    )
    await callback.answer()


@router.callback_query(F.data == "words:add")
async def on_add_words(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Navigate to word lists screen for adding words."""
    logger.debug(f"{__name__}:user:{db_user.username}")
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    # Get word lists for user's current language pair
    source_lang, _ = get_language_pair(db_user.language_pair)
    word_lists = get_word_lists_by_language(source_lang)
    ui_lang = db_user.ui_language.value

    if not word_lists:
        await safe_edit_or_send(
            message,
            text=i18n.get("lists-empty"),
            reply_markup=get_main_menu_keyboard(i18n),
        )
        await callback.answer()
        return

    await safe_edit_or_send(
        message,
        text=i18n.get("lists-title"),
        reply_markup=get_word_lists_keyboard(i18n, word_lists, ui_lang),
    )
    await callback.answer()


@router.callback_query(F.data == "stats:show")
async def on_coming_soon(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    # Placeholder for future functionality (Phase 5)
    logger.debug(f"{__name__}:user:{db_user.username}")
    await callback.answer(text=i18n.get("coming-soon"), show_alert=True)
