from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram_i18n import I18nContext


def get_main_reply_keyboard(i18n: I18nContext) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=i18n.get("btn-learn")),
                KeyboardButton(text=i18n.get("btn-review")),
                KeyboardButton(text=i18n.get("btn-menu")),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
