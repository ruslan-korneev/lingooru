"""Audio service for generating and retrieving word pronunciations."""

from uuid import UUID

import httpx
from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.audio.clients import get_gtts_client, get_s3_client
from src.modules.vocabulary.models import Word


class AudioService:
    """Service for audio generation and retrieval."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._s3 = get_s3_client()
        self._gtts = get_gtts_client()

    async def get_audio_url(self, word_id: UUID) -> str | None:
        """Get audio URL for word, generating if needed.

        Args:
            word_id: UUID of the word

        Returns:
            URL to the audio file or None if unavailable
        """
        word = await self._get_word(word_id)
        if not word:
            return None

        # Already has audio URL
        if word.audio_url:
            return word.audio_url

        # Generate and cache
        return await self._generate_and_cache(word)

    async def get_audio_bytes(self, word_id: UUID) -> bytes | None:
        """Get audio bytes for sending to Telegram.

        Args:
            word_id: UUID of the word

        Returns:
            Audio bytes or None if unavailable
        """
        url = await self.get_audio_url(word_id)
        if not url:
            return None

        return await self._download_audio(url)

    async def _get_word(self, word_id: UUID) -> Word | None:
        """Get word from database."""
        query = select(Word).where(Word.id == word_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def _generate_and_cache(self, word: Word) -> str | None:
        """Generate audio via gTTS and upload to S3.

        Args:
            word: Word model instance

        Returns:
            URL to the uploaded audio or None on failure
        """
        # Only generate for supported languages
        if word.language.value not in ("en", "ko"):
            logger.warning(f"Language {word.language} not supported for TTS")
            return None

        try:
            # Generate audio
            audio_bytes = await self._gtts.generate(
                text=word.text,
                language=word.language.value,
            )

            # Upload to S3
            key = f"words/{word.id}.mp3"
            url = await self._s3.upload_audio(audio_bytes, key)

            # Update word record
            await self._update_word_audio(
                word_id=word.id,
                audio_url=url,
                audio_source="gtts",
            )

        except Exception as e:
            logger.error(f"Failed to generate audio for word {word.id}: {e}")
            return None
        else:
            return url

    async def _update_word_audio(
        self,
        word_id: UUID,
        audio_url: str,
        audio_source: str,
    ) -> None:
        """Update word with audio URL and source."""
        query = (
            update(Word)
            .where(Word.id == word_id)
            .values(audio_url=audio_url, audio_source=audio_source)
        )
        await self._session.execute(query)
        await self._session.flush()

    async def _download_audio(self, url: str) -> bytes | None:
        """Download audio from URL."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to download audio: HTTP {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Failed to download audio from {url}: {e}")
            return None
