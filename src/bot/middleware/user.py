from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from src.db.session import AsyncSessionMaker
from src.modules.users.dto import UserCreateDTO
from src.modules.users.services import UserService


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_tg = None
        if (isinstance(event, Message) and event.from_user) or (isinstance(event, CallbackQuery) and event.from_user):
            user_tg = event.from_user

        if user_tg:
            async with AsyncSessionMaker() as session:
                service = UserService(session)
                dto = UserCreateDTO(
                    telegram_id=user_tg.id,
                    username=user_tg.username,
                    first_name=user_tg.first_name,
                )
                user, _ = await service.get_or_create(dto)
                await session.commit()
                data["db_user"] = user

        return await handler(event, data)
