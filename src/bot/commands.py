"""Bot commands setup for Telegram command menu."""

from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault
from loguru import logger


async def set_bot_commands(bot: Bot) -> None:
    """Register bot commands in Telegram's command menu.

    This sets up the commands that appear when users click the menu button (☰)
    next to the input field in Telegram.
    """
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="menu", description="Show main menu"),
    ]

    await bot.set_my_commands(commands=commands, scope=BotCommandScopeDefault())
    logger.info(f"Bot commands registered: {[c.command for c in commands]}")
