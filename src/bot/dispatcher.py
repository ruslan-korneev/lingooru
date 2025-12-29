from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores.fluent_runtime_core import FluentRuntimeCore

from src.bot.handlers import menu_router, start_router
from src.bot.middleware.i18n import UserLocaleManager
from src.bot.middleware.user import UserMiddleware
from src.config import settings


def create_bot() -> Bot:
    return Bot(
        token=settings.telegram.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()

    # Include routers
    dp.include_router(start_router)
    dp.include_router(menu_router)

    # Setup user middleware (must be before i18n)
    dp.message.outer_middleware(UserMiddleware())
    dp.callback_query.outer_middleware(UserMiddleware())

    # Setup i18n middleware
    i18n_middleware = I18nMiddleware(
        core=FluentRuntimeCore(
            path="src/bot/locales/{locale}",
            default_locale="ru",
        ),
        manager=UserLocaleManager(),
        default_locale="ru",
    )
    i18n_middleware.setup(dispatcher=dp)

    return dp


class _BotHolder:
    """Singleton holder for bot and dispatcher instances."""

    _bot: Bot | None = None
    _dispatcher: Dispatcher | None = None

    @classmethod
    def get_bot(cls) -> Bot:
        if cls._bot is None:
            cls._bot = create_bot()
        return cls._bot

    @classmethod
    def get_dispatcher(cls) -> Dispatcher:
        if cls._dispatcher is None:
            cls._dispatcher = create_dispatcher()
        return cls._dispatcher


def get_bot() -> Bot:
    return _BotHolder.get_bot()


def get_dispatcher() -> Dispatcher:
    return _BotHolder.get_dispatcher()
