from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext

from src.modules.vocabulary.word_lists import ThematicWordList


def get_word_lists_keyboard(
    i18n: I18nContext,
    word_lists: list[ThematicWordList],
    lang: str,
    added_list_ids: set[str] | None = None,
) -> InlineKeyboardMarkup:
    """Keyboard with available word lists."""
    builder = InlineKeyboardBuilder()
    added_list_ids = added_list_ids or set()

    for wl in word_lists:
        name = wl.get_name(lang)
        is_added = wl.id in added_list_ids
        display_name = f"✅ {name}" if is_added else name

        builder.row(
            InlineKeyboardButton(
                text=display_name,
                callback_data=f"lists:preview:{wl.id}",
            )
        )

    builder.row(
        InlineKeyboardButton(text=i18n.get("btn-back"), callback_data="menu:main"),
    )

    return builder.as_markup()


def get_word_list_preview_keyboard(
    i18n: I18nContext,
    list_id: str,
    *,
    is_added: bool = False,
) -> InlineKeyboardMarkup:
    """Preview keyboard for a word list."""
    builder = InlineKeyboardBuilder()

    if is_added:
        builder.row(
            InlineKeyboardButton(
                text=i18n.get("btn-list-added"),
                callback_data="noop",
            ),
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text=i18n.get("btn-add-list"),
                callback_data=f"lists:add:{list_id}",
            ),
        )
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-back"),
            callback_data="lists:show",
        ),
    )

    return builder.as_markup()


def get_list_added_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Keyboard shown after adding words from a list."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-learn"),
            callback_data="learn:start",
        ),
        InlineKeyboardButton(
            text=i18n.get("btn-more-lists"),
            callback_data="lists:show",
        ),
    )
    builder.row(
        InlineKeyboardButton(text=i18n.get("btn-menu"), callback_data="menu:main"),
    )

    return builder.as_markup()
