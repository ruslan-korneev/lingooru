from src.bot.handlers.audio import router as audio_router
from src.bot.handlers.learn import router as learn_router
from src.bot.handlers.menu import router as menu_router
from src.bot.handlers.review import router as review_router
from src.bot.handlers.start import router as start_router
from src.bot.handlers.teaching import router as teaching_router
from src.bot.handlers.vocabulary import router as vocabulary_router
from src.bot.handlers.voice import router as voice_router
from src.bot.handlers.word_lists import router as word_lists_router

__all__ = (
    "audio_router",
    "learn_router",
    "menu_router",
    "review_router",
    "start_router",
    "teaching_router",
    "vocabulary_router",
    "voice_router",
    "word_lists_router",
)
