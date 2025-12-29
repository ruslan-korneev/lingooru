from typing import TYPE_CHECKING, Any

from aiogram.types import TelegramObject
from aiogram.types import User as TelegramUser
from aiogram_i18n.managers import BaseManager

if TYPE_CHECKING:
    from src.modules.users.dto import UserReadDTO


class UserLocaleManager(BaseManager):
    async def get_locale(
        self,
        event: TelegramObject,  # noqa: ARG002
        event_from_user: TelegramUser | None = None,
        db_user: "UserReadDTO | None" = None,
        **_kwargs: Any,
    ) -> str:
        if db_user:
            return db_user.ui_language.value

        # Fallback to Telegram user language
        if (
            event_from_user
            and event_from_user.language_code
            and event_from_user.language_code in ("ru", "en", "ko")
        ):
            return event_from_user.language_code

        return "ru"

    async def set_locale(
        self,
        locale: str,
        event: TelegramObject | None = None,
        **_kwargs: Any,
    ) -> None:
        # Locale is already saved to DB in the handler
        pass
