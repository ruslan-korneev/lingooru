"""Bot info storage for cached bot information."""

from aiogram import Bot
from loguru import logger

from src.config import settings


class _BotInfo:
    """Singleton storage for bot information."""

    _username: str | None = None

    @classmethod
    async def init(cls, bot: Bot) -> None:
        """Fetch and cache bot info from Telegram API."""
        me = await bot.get_me()
        cls._username = me.username
        logger.info(f"Bot info initialized: @{cls._username}")

    @classmethod
    def get_username(cls) -> str:
        """Get bot username. Falls back to config if not initialized."""
        if cls._username is None:
            logger.warning(f"Bot username not initialized, using fallback: {settings.telegram.bot_username}")
            return settings.telegram.bot_username
        return cls._username


async def init_bot_info(bot: Bot) -> None:
    """Initialize bot info by fetching from Telegram API."""
    await _BotInfo.init(bot)


def get_bot_username() -> str:
    """Get bot username. Falls back to config if not initialized."""
    return _BotInfo.get_username()
