"""Keyboards for voice pronunciation practice."""

from uuid import UUID

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext


def get_voice_prompt_keyboard(
    i18n: I18nContext,
    word_id: UUID | None = None,
) -> InlineKeyboardMarkup:
    """Keyboard for word pronunciation prompt."""
    builder = InlineKeyboardBuilder()

    # Add audio button if word_id provided
    if word_id:
        builder.row(
            InlineKeyboardButton(
                text=i18n.get("btn-play-audio"),
                callback_data=f"audio:play:voice:{word_id}",
            )
        )

    builder.row(
        InlineKeyboardButton(text=i18n.get("btn-skip"), callback_data="voice:skip"),
    )
    builder.row(
        InlineKeyboardButton(text=i18n.get("btn-menu"), callback_data="menu:main"),
    )

    return builder.as_markup()


def get_voice_result_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Keyboard for pronunciation result screen."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-voice-retry"),
            callback_data="voice:retry",
        ),
        InlineKeyboardButton(
            text=i18n.get("btn-voice-next"),
            callback_data="voice:next",
        ),
    )
    builder.row(
        InlineKeyboardButton(text=i18n.get("btn-menu"), callback_data="menu:main"),
    )

    return builder.as_markup()


def get_voice_complete_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Keyboard for session completion."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-voice-again"),
            callback_data="voice:start",
        ),
        InlineKeyboardButton(
            text=i18n.get("btn-learn"),
            callback_data="learn:start",
        ),
    )
    builder.row(
        InlineKeyboardButton(text=i18n.get("btn-menu"), callback_data="menu:main"),
    )

    return builder.as_markup()


def get_voice_no_words_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Keyboard when no words available for practice."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-add-words"),
            callback_data="word:add",
        ),
        InlineKeyboardButton(
            text=i18n.get("btn-learn"),
            callback_data="learn:start",
        ),
    )
    builder.row(
        InlineKeyboardButton(text=i18n.get("btn-menu"), callback_data="menu:main"),
    )

    return builder.as_markup()
