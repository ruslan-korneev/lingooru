from src.bot.handlers.learn import router as learn_router
from src.bot.handlers.menu import router as menu_router
from src.bot.handlers.start import router as start_router
from src.bot.handlers.vocabulary import router as vocabulary_router
from src.bot.handlers.word_lists import router as word_lists_router

__all__ = (
    "learn_router",
    "menu_router",
    "start_router",
    "vocabulary_router",
    "word_lists_router",
)
