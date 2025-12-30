"""Google Text-to-Speech client using gTTS library."""

import asyncio
import io

from gtts import gTTS
from gtts.tts import gTTSError
from loguru import logger

from src.modules.vocabulary.enums import Language


class GTTSClient:
    """Text-to-speech client using gTTS library."""

    async def generate(
        self,
        text: str,
        language: Language,
    ) -> bytes:
        """Generate speech audio for text.

        Args:
            text: Text to convert to speech
            language: Target language

        Returns:
            Audio bytes in MP3 format
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._generate_sync, text, language.value)

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
