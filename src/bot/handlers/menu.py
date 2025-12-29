from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram_i18n import I18nContext

from src.bot.keyboards.menu import get_main_menu_keyboard, get_settings_keyboard
from src.modules.users.dto import UserReadDTO

router = Router(name="menu")

# Reply keyboard button texts for all languages
MENU_BUTTONS = {"📋 Меню", "📋 Menu", "📋 메뉴"}
LEARN_BUTTONS = {"📚 Учить", "📚 Learn", "📚 학습"}
REVIEW_BUTTONS = {"🔄 Повторять", "🔄 Review", "🔄 복습"}


@router.message(F.text.in_(MENU_BUTTONS))
async def on_menu_button(
    message: Message,
    i18n: I18nContext,
    db_user: UserReadDTO,  # noqa: ARG001
) -> None:
    text = (
        f"{i18n.get('menu-title')}\n"
        f"{i18n.get('menu-subtitle')}\n\n"
        f"{i18n.get('menu-stats', words=0)}\n"
        f"{i18n.get('menu-streak', days=0)}"
    )
    await message.answer(
        text=text,
        reply_markup=get_main_menu_keyboard(i18n),
    )


@router.message(F.text.in_(LEARN_BUTTONS))
async def on_learn_button(
    message: Message,
    i18n: I18nContext,
    db_user: UserReadDTO,  # noqa: ARG001
) -> None:
    # Placeholder for learning functionality (Phase 1)
    await message.answer(text=i18n.get("coming-soon"))


@router.message(F.text.in_(REVIEW_BUTTONS))
async def on_review_button(
    message: Message,
    i18n: I18nContext,
    db_user: UserReadDTO,  # noqa: ARG001
) -> None:
    # Placeholder for review functionality (Phase 2)
    await message.answer(text=i18n.get("coming-soon"))


@router.callback_query(F.data == "menu:main")
async def on_main_menu(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,  # noqa: ARG001
) -> None:
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    text = (
        f"{i18n.get('menu-title')}\n"
        f"{i18n.get('menu-subtitle')}\n\n"
        f"{i18n.get('menu-stats', words=0)}\n"
        f"{i18n.get('menu-streak', days=0)}"
    )
    await message.edit_text(
        text=text,
        reply_markup=get_main_menu_keyboard(i18n),
    )
    await callback.answer()


@router.callback_query(F.data == "settings:main")
async def on_settings(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
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

    pair_name = {
        "en_ru": "EN → RU",
        "ko_ru": "KO → RU",
    }.get(db_user.language_pair.value, db_user.language_pair.value)

    text = (
        f"{i18n.get('settings-title')}\n\n"
        f"{i18n.get('settings-lang', lang=lang_name)}\n"
        f"{i18n.get('settings-pair', pair=pair_name)}"
    )
    await message.edit_text(
        text=text,
        reply_markup=get_settings_keyboard(i18n),
    )
    await callback.answer()


@router.callback_query(F.data == "settings:lang")
async def on_change_language(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,  # noqa: ARG001
) -> None:
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    from src.bot.keyboards.menu import get_language_selection_keyboard

    await message.edit_text(
        text=i18n.get("welcome-choose-lang"),
        reply_markup=get_language_selection_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "settings:pair")
async def on_change_pair(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,  # noqa: ARG001
) -> None:
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    from src.bot.keyboards.menu import get_pair_selection_keyboard

    await message.edit_text(
        text=i18n.get("welcome-choose-pair"),
        reply_markup=get_pair_selection_keyboard(i18n),
    )
    await callback.answer()


@router.callback_query(F.data.in_({"learn:start", "review:start", "stats:show"}))
async def on_coming_soon(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,  # noqa: ARG001
) -> None:
    # Placeholder for future functionality
    await callback.answer(text=i18n.get("coming-soon"), show_alert=True)
