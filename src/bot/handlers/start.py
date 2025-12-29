from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from aiogram_i18n import I18nContext

from src.bot.keyboards.menu import (
    get_language_selection_keyboard,
    get_main_menu_keyboard,
    get_pair_selection_keyboard,
)
from src.bot.keyboards.reply import get_main_reply_keyboard
from src.db.session import AsyncSessionMaker
from src.modules.users.dto import UserReadDTO, UserUpdateDTO
from src.modules.users.models import LanguagePair, UILanguage
from src.modules.users.services import UserService

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    i18n: I18nContext,
    db_user: UserReadDTO,  # noqa: ARG001
) -> None:
    # Show language selection for all /start commands
    # Users can change settings from main menu later
    await message.answer(
        text=f"{i18n.get('welcome')}\n\n{i18n.get('welcome-choose-lang')}",
        reply_markup=get_language_selection_keyboard(),
    )


async def show_main_menu(
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
    # Set the reply keyboard
    await message.answer(
        text="👇",
        reply_markup=get_main_reply_keyboard(i18n),
    )


@router.callback_query(F.data.startswith("settings:lang:"))
async def on_language_selected(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    if not callback.data or not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    lang_code = callback.data.split(":")[-1]

    # Update user language in database
    async with AsyncSessionMaker() as session:
        service = UserService(session)
        await service.update(
            db_user.id,
            UserUpdateDTO(ui_language=UILanguage(lang_code)),
        )
        await session.commit()

    # Set new locale for i18n
    await i18n.set_locale(lang_code)

    # Show language pair selection
    await message.edit_text(
        text=i18n.get("welcome-choose-pair"),
        reply_markup=get_pair_selection_keyboard(i18n),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("settings:pair:"))
async def on_pair_selected(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    if not callback.data or not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    pair_code = callback.data.split(":")[-1]

    # Update user language pair in database
    async with AsyncSessionMaker() as session:
        service = UserService(session)
        updated_user = await service.update(
            db_user.id,
            UserUpdateDTO(language_pair=LanguagePair(pair_code)),
        )
        await session.commit()

    # Show confirmation
    await message.edit_text(
        text=i18n.get("settings-saved"),
    )

    # Send main menu as new message
    await show_main_menu(message, i18n, updated_user)
    await callback.answer()
