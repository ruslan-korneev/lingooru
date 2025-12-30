from uuid import UUID

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext

from src.bot.utils.flags import get_flag
from src.modules.vocabulary.enums import Language


def get_language_selection_keyboard(
    i18n: I18nContext,
    counts: dict[Language, int],
) -> InlineKeyboardMarkup:
    """Keyboard for selecting learning language with word counts."""
    builder = InlineKeyboardBuilder()

    if counts.get(Language.EN, 0) > 0:
        builder.row(
            InlineKeyboardButton(
                text=f"{get_flag(Language.EN)} English ({counts[Language.EN]})",
                callback_data="learn:lang:en",
            )
        )

    if counts.get(Language.KO, 0) > 0:
        builder.row(
            InlineKeyboardButton(
                text=f"{get_flag(Language.KO)} Korean ({counts[Language.KO]})",
                callback_data="learn:lang:ko",
            )
        )

    total = sum(counts.values())
    if total > 0:
        builder.row(
            InlineKeyboardButton(
                text=f"🌍 {i18n.get('btn-mix')} ({total})",
                callback_data="learn:lang:mix",
            )
        )

    builder.row(
        InlineKeyboardButton(text=i18n.get("btn-menu"), callback_data="menu:main"),
    )

    return builder.as_markup()


def get_learning_card_keyboard(
    i18n: I18nContext,
    word_id: UUID | None = None,
) -> InlineKeyboardMarkup:
    """Keyboard for learning card with Know/Hard/Forgot buttons."""
    builder = InlineKeyboardBuilder()

    # Add audio button if word_id provided
    if word_id:
        builder.row(
            InlineKeyboardButton(
                text=i18n.get("btn-play-audio"),
                callback_data=f"audio:play:learn:{word_id}",
            )
        )

    builder.row(
        InlineKeyboardButton(text=i18n.get("btn-know"), callback_data="learn:know"),
        InlineKeyboardButton(text=i18n.get("btn-hard"), callback_data="learn:hard"),
        InlineKeyboardButton(text=i18n.get("btn-forgot"), callback_data="learn:forgot"),
    )
    builder.row(
        InlineKeyboardButton(text=i18n.get("btn-skip"), callback_data="learn:skip"),
        InlineKeyboardButton(text=i18n.get("btn-menu"), callback_data="menu:main"),
    )

    return builder.as_markup()


def get_word_added_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Keyboard shown after word is added."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-learn"),
            callback_data="learn:start",
        ),
        InlineKeyboardButton(
            text=i18n.get("btn-add-more"),
            callback_data="word:add",
        ),
    )
    builder.row(
        InlineKeyboardButton(text=i18n.get("btn-menu"), callback_data="menu:main"),
    )

    return builder.as_markup()


def get_word_not_found_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Keyboard when no words to learn."""
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


def get_learning_complete_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Keyboard shown after learning session is complete."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-learn-again"),
            callback_data="learn:start",
        ),
        InlineKeyboardButton(
            text=i18n.get("btn-add-words"),
            callback_data="word:add",
        ),
    )
    builder.row(
        InlineKeyboardButton(text=i18n.get("btn-menu"), callback_data="menu:main"),
    )

    return builder.as_markup()
