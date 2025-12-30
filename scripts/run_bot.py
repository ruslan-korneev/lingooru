#!/usr/bin/env python3
"""Run Telegram bot in polling mode for development."""

import asyncio

from loguru import logger

from src.bot.bot_info import init_bot_info
from src.bot.dispatcher import get_bot, get_dispatcher, get_i18n_middleware


async def main() -> None:
    """Start bot in polling mode."""
    bot = get_bot()
    dp = get_dispatcher()
    i18n = get_i18n_middleware()

    # Initialize i18n (load locales)
    await i18n.core.startup()

    # Initialize bot info (username, etc.)
    await init_bot_info(bot)

    # Delete any existing webhook
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook deleted, starting polling...")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
