"""Voice service - business logic for pronunciation practice."""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vocabulary.models import Language
from src.modules.voice.dto import (
    PronunciationLogCreateDTO,
    PronunciationLogReadDTO,
    PronunciationSessionStatsDTO,
    WordForPronunciationDTO,
)
from src.modules.voice.openai_client import get_openai_client
from src.modules.voice.repositories import PronunciationLogRepository


class VoiceService:
    """Service for pronunciation practice functionality."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._log_repo = PronunciationLogRepository(session)
        self._openai = get_openai_client()

    async def get_words_for_pronunciation(
        self,
        user_id: UUID,
        source_language: Language,
        limit: int = 10,
    ) -> Sequence[WordForPronunciationDTO]:
        """Get learned words for pronunciation practice.

        Args:
            user_id: User's ID
            source_language: Language to practice (EN, KO)
            limit: Maximum number of words to return

        Returns:
            List of words with pronunciation details
        """
        return await self._log_repo.get_words_for_pronunciation(
            user_id=user_id,
            source_language=source_language,
            limit=limit,
        )

    async def process_voice_message(
        self,
        user_id: UUID,
        word_id: UUID,
        expected_text: str,
        audio_bytes: bytes,
        language: str,
        phonetic: str | None = None,
    ) -> PronunciationLogReadDTO:
        """Process voice message and return pronunciation feedback.

        Args:
            user_id: User's ID
            word_id: Word being pronounced
            expected_text: Expected word text
            audio_bytes: Audio data from Telegram voice message
            language: Language code (en, ko)
            phonetic: Optional IPA transcription

        Returns:
            PronunciationLogReadDTO with transcription, rating, and feedback
        """
        # 1. Transcribe audio via Whisper
        transcription = await self._openai.transcribe(
            audio_bytes=audio_bytes,
            language=language,
        )

        # 2. Check pronunciation via GPT-4o
        evaluation = await self._openai.check_pronunciation(
            expected=expected_text,
            transcribed=transcription.text,
            language=language,
            phonetic=phonetic,
        )

        # 3. Save pronunciation log
        log_dto = PronunciationLogCreateDTO(
            user_id=user_id,
            word_id=word_id,
            transcribed_text=transcription.text,
            expected_text=expected_text,
            rating=evaluation.rating,
            feedback=evaluation.feedback,
            audio_duration_seconds=transcription.duration_seconds,
        )
        return await self._log_repo.save(log_dto)

    async def get_session_stats(
        self,
        log_ids: list[UUID],
        session_start: datetime,
    ) -> PronunciationSessionStatsDTO:
        """Get statistics for completed pronunciation session.

        Args:
            log_ids: List of pronunciation log IDs from this session
            session_start: When the session started

        Returns:
            Session statistics with total, average rating, and time spent
        """
        avg_rating = await self._log_repo.get_average_rating(log_ids)
        time_spent = int((datetime.now(tz=UTC) - session_start).total_seconds())

        return PronunciationSessionStatsDTO(
            total_practiced=len(log_ids),
            average_rating=round(avg_rating, 1),
            time_spent_seconds=time_spent,
        )

    async def get_user_stats(self, user_id: UUID) -> tuple[int, float]:
        """Get user's overall pronunciation statistics.

        Args:
            user_id: User's ID

        Returns:
            Tuple of (total attempts, average rating)
        """
        return await self._log_repo.get_user_stats(user_id)
