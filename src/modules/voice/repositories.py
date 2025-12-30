"""Voice module repositories for PronunciationLog."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func as sql_func

from src.core.types.repositories import BaseRepository
from src.modules.vocabulary.enums import Language
from src.modules.vocabulary.models import UserWord, Word
from src.modules.voice.dto import (
    PronunciationLogCreateDTO,
    PronunciationLogReadDTO,
    WordForPronunciationDTO,
)
from src.modules.voice.models import PronunciationLog


class PronunciationLogRepository(BaseRepository[PronunciationLog, PronunciationLogCreateDTO, PronunciationLogReadDTO]):
    _model = PronunciationLog
    _create_dto = PronunciationLogCreateDTO
    _read_dto = PronunciationLogReadDTO

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_words_for_pronunciation(
        self,
        user_id: UUID,
        source_language: Language,
        limit: int = 10,
    ) -> Sequence[WordForPronunciationDTO]:
        """Get user's learned words for pronunciation practice."""
        query = (
            select(
                Word.id,
                UserWord.id.label("user_word_id"),
                Word.text,
                Word.phonetic,
                Word.audio_url,
                Word.language,
            )
            .join(UserWord, Word.id == UserWord.word_id)
            .where(
                UserWord.user_id == user_id,
                UserWord.is_learned == True,  # noqa: E712
                Word.language == source_language,
            )
            .order_by(sql_func.random())
            .limit(limit)
        )
        result = await self._session.execute(query)
        return [
            WordForPronunciationDTO(
                id=row.id,
                user_word_id=row.user_word_id,
                text=row.text,
                phonetic=row.phonetic,
                audio_url=row.audio_url,
                language=row.language.value,
            )
            for row in result.all()
        ]

    async def get_average_rating(self, log_ids: list[UUID]) -> float:
        """Calculate average rating for a set of pronunciation logs."""
        if not log_ids:
            return 0.0

        query = select(func.avg(self._model.rating)).where(self._model.id.in_(log_ids))
        result = await self._session.execute(query)
        avg = result.scalar_one_or_none()
        return float(avg) if avg else 0.0

    async def get_user_stats(
        self,
        user_id: UUID,
    ) -> tuple[int, float]:
        """Get total pronunciation attempts and average rating for user."""
        query = select(
            func.count(self._model.id),
            func.avg(self._model.rating),
        ).where(self._model.user_id == user_id)
        result = await self._session.execute(query)
        row = result.one()
        return int(row[0]), float(row[1]) if row[1] else 0.0
