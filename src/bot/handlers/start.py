from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message
from aiogram_i18n import I18nContext

from src.bot.handlers.menu import _build_menu_text
from src.bot.handlers.teaching import handle_deep_link_join
from src.bot.keyboards.menu import (
    get_language_selection_keyboard,
    get_main_menu_keyboard,
    get_pair_selection_keyboard,
)
from src.bot.utils import (
    CALLBACK_VALUE_INDEX,
    extract_callback_message,
    format_greeting,
    get_random_greeting,
    parse_callback_param,
)
from src.db.session import AsyncSessionMaker
from src.modules.users.dto import UserReadDTO, UserUpdateDTO
from src.modules.users.enums import LanguagePair, UILanguage
from src.modules.users.services import UserService

router = Router(name="start")

DEEP_LINK_JOIN_PREFIX = "join_"


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    i18n: I18nContext,
    db_user: UserReadDTO,
    command: CommandObject,
) -> None:
    # Handle deep link for joining a teacher
    if command.args and command.args.startswith(DEEP_LINK_JOIN_PREFIX):
        invite_code = command.args[len(DEEP_LINK_JOIN_PREFIX) :]
        handled = await handle_deep_link_join(message, i18n, db_user, invite_code)
        if handled:
            return

    # Show language selection for all /start commands
    # Users can change settings from main menu later
    greeting = get_random_greeting()
    greeting_text = format_greeting(greeting)

    await message.answer(
        text=f"{greeting_text}\n\n{i18n.get('welcome')}\n\n{i18n.get('welcome-choose-lang')}",
        reply_markup=get_language_selection_keyboard(),
    )


@router.callback_query(F.data.startswith("settings:lang:"))
async def on_language_selected(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    message = extract_callback_message(callback)
    if message is None:
        return

    lang_code = parse_callback_param(callback.data, CALLBACK_VALUE_INDEX)

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
    message = extract_callback_message(callback)
    if message is None:
        return

    pair_code = parse_callback_param(callback.data, CALLBACK_VALUE_INDEX)

    # Update user language pair in database
    async with AsyncSessionMaker() as session:
        service = UserService(session)
        updated_user = await service.update(
            db_user.id,
            UserUpdateDTO(language_pair=LanguagePair(pair_code)),
        )
        await session.commit()

    # Show main menu directly
    text = await _build_menu_text(i18n, updated_user)
    await message.edit_text(
        text=text,
        reply_markup=get_main_menu_keyboard(i18n),
    )
    await callback.answer()
