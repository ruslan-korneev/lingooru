#!/usr/bin/env python3
"""Run Telegram bot in polling mode for development."""

import asyncio

from loguru import logger

from src.bot.dispatcher import create_bot, create_dispatcher


async def main() -> None:
    """Start bot in polling mode."""
    bot = create_bot()
    dp = create_dispatcher()

    # Delete any existing webhook
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook deleted, starting polling...")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
