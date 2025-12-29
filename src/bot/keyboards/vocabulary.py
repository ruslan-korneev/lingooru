from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext

from src.bot.utils.flags import get_flag
from src.modules.vocabulary.models import Language


def get_vocabulary_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Basic vocabulary keyboard."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-add-words"),
            callback_data="word:add",
        ),
        InlineKeyboardButton(
            text=i18n.get("btn-word-lists"),
            callback_data="lists:show",
        ),
    )
    builder.row(
        InlineKeyboardButton(text=i18n.get("btn-menu"), callback_data="menu:main"),
    )

    return builder.as_markup()


def get_vocabulary_pagination_keyboard(
    i18n: I18nContext,
    current_page: int,
    total_pages: int,
    current_filter: Language | None = None,
) -> InlineKeyboardMarkup:
    """Vocabulary list with pagination and language filter."""
    builder = InlineKeyboardBuilder()

    # Language filter row
    filter_buttons = []
    all_selected = "✓ " if current_filter is None else ""
    filter_buttons.append(
        InlineKeyboardButton(
            text=f"{all_selected}🌍",
            callback_data="vocab:filter:all",
        )
    )

    en_selected = "✓ " if current_filter == Language.EN else ""
    filter_buttons.append(
        InlineKeyboardButton(
            text=f"{en_selected}{get_flag(Language.EN)}",
            callback_data="vocab:filter:en",
        )
    )

    ko_selected = "✓ " if current_filter == Language.KO else ""
    filter_buttons.append(
        InlineKeyboardButton(
            text=f"{ko_selected}{get_flag(Language.KO)}",
            callback_data="vocab:filter:ko",
        )
    )

    builder.row(*filter_buttons)

    # Pagination row
    nav_buttons = []
    if current_page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=f"vocab:page:{current_page - 1}",
            )
        )

    nav_buttons.append(
        InlineKeyboardButton(
            text=f"{current_page + 1}/{total_pages}",
            callback_data="noop",
        )
    )

    if current_page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=f"vocab:page:{current_page + 1}",
            )
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    # Actions row
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-add-words"),
            callback_data="word:add",
        ),
        InlineKeyboardButton(text=i18n.get("btn-menu"), callback_data="menu:main"),
    )

    return builder.as_markup()
