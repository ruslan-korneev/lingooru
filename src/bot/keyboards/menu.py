from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext


def get_language_selection_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="settings:lang:ru"),
    )
    builder.row(
        InlineKeyboardButton(text="🇬🇧 English", callback_data="settings:lang:en"),
    )
    builder.row(
        InlineKeyboardButton(text="🇰🇷 한국어", callback_data="settings:lang:ko"),
    )
    return builder.as_markup()


def get_pair_selection_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("pair-en-ru"),
            callback_data="settings:pair:en_ru",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("pair-ko-ru"),
            callback_data="settings:pair:ko_ru",
        ),
    )
    return builder.as_markup()


def get_main_menu_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=i18n.get("btn-learn"), callback_data="learn:start"),
        InlineKeyboardButton(text=i18n.get("btn-review"), callback_data="review:start"),
    )
    builder.row(
        InlineKeyboardButton(text=i18n.get("btn-stats"), callback_data="stats:show"),
        InlineKeyboardButton(text=i18n.get("btn-settings"), callback_data="settings:main"),
    )
    return builder.as_markup()


def get_settings_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=i18n.get("btn-lang"), callback_data="settings:lang"),
        InlineKeyboardButton(text=i18n.get("btn-pair"), callback_data="settings:pair"),
    )
    builder.row(
        InlineKeyboardButton(text=i18n.get("btn-back"), callback_data="menu:main"),
    )
    return builder.as_markup()
