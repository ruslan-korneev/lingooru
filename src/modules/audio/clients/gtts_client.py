"""Google Text-to-Speech client using gTTS library."""

import asyncio
import io
from typing import ClassVar

from gtts import gTTS
from gtts.tts import gTTSError
from loguru import logger


class GTTSClient:
    """Text-to-speech client using gTTS library."""

    LANGUAGE_MAP: ClassVar[dict[str, str]] = {
        "en": "en",
        "ko": "ko",
        "ru": "ru",
    }

    async def generate(
        self,
        text: str,
        language: str,
    ) -> bytes:
        """Generate speech audio for text.

        Args:
            text: Text to convert to speech
            language: Language code (en, ko, ru)

        Returns:
            Audio bytes in MP3 format
        """
        lang_code = self.LANGUAGE_MAP.get(language, "en")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._generate_sync, text, lang_code)

    def _generate_sync(self, text: str, language: str) -> bytes:
        """Synchronous generation using gTTS."""
        try:
            tts = gTTS(text=text, lang=language)
            buffer = io.BytesIO()
            tts.write_to_fp(buffer)
            buffer.seek(0)
            return buffer.read()
        except gTTSError as e:
            logger.error(f"gTTS generation failed for '{text}' ({language}): {e}")
            raise


class _GTTSClientHolder:
    """Holder for singleton gTTS client instance."""

    _instance: GTTSClient | None = None

    @classmethod
    def get(cls) -> GTTSClient:
        if cls._instance is None:
            cls._instance = GTTSClient()
        return cls._instance


def get_gtts_client() -> GTTSClient:
    """Get the singleton gTTS client instance."""
    return _GTTSClientHolder.get()
