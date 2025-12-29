"""Review keyboards for spaced repetition sessions."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext


def get_review_start_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Keyboard for review start screen."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-begin-review"),
            callback_data="review:begin",
        )
    )
    builder.row(
        InlineKeyboardButton(text=i18n.get("btn-menu"), callback_data="menu:main"),
    )

    return builder.as_markup()


def get_review_show_answer_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Keyboard with 'Show Answer' button."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-show-answer"),
            callback_data="review:show",
        )
    )
    builder.row(
        InlineKeyboardButton(text=i18n.get("btn-menu"), callback_data="menu:main"),
    )

    return builder.as_markup()


def get_review_rating_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Keyboard with quality rating buttons 1-5."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="1️⃣", callback_data="review:rate:1"),
        InlineKeyboardButton(text="2️⃣", callback_data="review:rate:2"),
        InlineKeyboardButton(text="3️⃣", callback_data="review:rate:3"),
        InlineKeyboardButton(text="4️⃣", callback_data="review:rate:4"),
        InlineKeyboardButton(text="5️⃣", callback_data="review:rate:5"),
    )
    builder.row(
        InlineKeyboardButton(text=i18n.get("btn-menu"), callback_data="menu:main"),
    )

    return builder.as_markup()


def get_review_complete_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Keyboard for session completion."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-review-again"),
            callback_data="review:start",
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
