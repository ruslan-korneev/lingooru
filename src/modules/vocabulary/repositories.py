from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import case, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.core.types.repositories import BaseRepository, PaginatedResult
from src.modules.vocabulary.dto import (
    TranslationCreateDTO,
    TranslationReadDTO,
    UserWordCreateDTO,
    UserWordListCreateDTO,
    UserWordListReadDTO,
    UserWordReadDTO,
    UserWordWithDetailsDTO,
    WordCreateDTO,
    WordReadDTO,
    WordWithTranslationDTO,
)
from src.modules.vocabulary.models import Language, Translation, UserWord, UserWordList, Word


class WordRepository(BaseRepository[Word, WordCreateDTO, WordReadDTO]):
    _model = Word
    _create_dto = WordCreateDTO
    _read_dto = WordReadDTO

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_id(self, word_id: UUID) -> WordReadDTO | None:
        query = select(self._model).where(self._model.id == word_id)
        result = await self._session.execute(query)
        instance = result.scalar_one_or_none()
        return self._read_dto.model_validate(instance) if instance else None

    async def get_by_text_and_language(
        self,
        text: str,
        language: Language,
    ) -> WordReadDTO | None:
        query = select(self._model).where(
            self._model.text == text.lower().strip(),
            self._model.language == language,
        )
        result = await self._session.execute(query)
        instance = result.scalar_one_or_none()
        return self._read_dto.model_validate(instance) if instance else None

    async def get_with_translation(
        self,
        word_id: UUID,
        target_language: Language,
    ) -> WordWithTranslationDTO | None:
        query = select(self._model).options(joinedload(self._model.translations)).where(self._model.id == word_id)
        result = await self._session.execute(query)
        word = result.unique().scalar_one_or_none()
        if not word:
            return None

        translation = next(
            (t for t in word.translations if t.target_language == target_language),
            None,
        )
        if not translation:
            return None

        return WordWithTranslationDTO(
            id=word.id,
            text=word.text,
            language=word.language,
            phonetic=word.phonetic,
            audio_url=word.audio_url,
            translation=translation.translated_text,
            example_sentence=translation.example_sentence,
        )


class TranslationRepository(BaseRepository[Translation, TranslationCreateDTO, TranslationReadDTO]):
    _model = Translation
    _create_dto = TranslationCreateDTO
    _read_dto = TranslationReadDTO

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_word_and_language(
        self,
        word_id: UUID,
        target_language: Language,
    ) -> TranslationReadDTO | None:
        query = select(self._model).where(
            self._model.word_id == word_id,
            self._model.target_language == target_language,
        )
        result = await self._session.execute(query)
        instance = result.scalar_one_or_none()
        return self._read_dto.model_validate(instance) if instance else None


class UserWordRepository(BaseRepository[UserWord, UserWordCreateDTO, UserWordReadDTO]):
    _model = UserWord
    _create_dto = UserWordCreateDTO
    _read_dto = UserWordReadDTO

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_user_and_word(
        self,
        user_id: UUID,
        word_id: UUID,
    ) -> UserWordReadDTO | None:
        query = select(self._model).where(
            self._model.user_id == user_id,
            self._model.word_id == word_id,
        )
        result = await self._session.execute(query)
        instance = result.scalar_one_or_none()
        return self._read_dto.model_validate(instance) if instance else None

    async def get_user_vocabulary_paginated(
        self,
        user_id: UUID,
        target_language: Language,
        limit: int = 10,
        offset: int = 0,
        learned_only: bool | None = None,
        source_language: Language | None = None,
    ) -> PaginatedResult[UserWordWithDetailsDTO]:
        # Base filters
        filters = [self._model.user_id == user_id]
        if learned_only is not None:
            filters.append(self._model.is_learned == learned_only)

        # Build base query with join for source_language filter
        base_query = select(self._model).join(self._model.word)
        if source_language is not None:
            filters.append(Word.language == source_language)

        # Count total
        count_query = select(func.count()).select_from(base_query.where(*filters).subquery())
        total_result = await self._session.execute(count_query)
        total = total_result.scalar_one()

        # Get paginated items with joins
        query = (
            base_query.options(joinedload(self._model.word).joinedload(Word.translations))
            .where(*filters)
            .order_by(self._model.added_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(query)
        user_words = result.unique().scalars().all()

        items = []
        for uw in user_words:
            translation = next(
                (t for t in uw.word.translations if t.target_language == target_language),
                None,
            )
            if translation:
                items.append(
                    UserWordWithDetailsDTO(
                        id=uw.id,
                        user_id=uw.user_id,
                        word=WordWithTranslationDTO(
                            id=uw.word.id,
                            text=uw.word.text,
                            language=uw.word.language,
                            phonetic=uw.word.phonetic,
                            audio_url=uw.word.audio_url,
                            translation=translation.translated_text,
                            example_sentence=translation.example_sentence,
                        ),
                        added_at=uw.added_at,
                        is_learned=uw.is_learned,
                    )
                )

        return PaginatedResult(items=items, total=total)

    async def get_words_for_learning(
        self,
        user_id: UUID,
        target_language: Language,
        source_language: Language | None = None,
        limit: int = 10,
    ) -> Sequence[UserWordWithDetailsDTO]:
        """Get unlearned words for learning session."""
        filters = [
            self._model.user_id == user_id,
            self._model.is_learned == False,  # noqa: E712
        ]

        # Build query with join for source_language filter
        base_query = select(self._model).join(self._model.word)
        if source_language is not None:
            filters.append(Word.language == source_language)

        query = (
            base_query.options(joinedload(self._model.word).joinedload(Word.translations))
            .where(*filters)
            .order_by(self._model.added_at)
            .limit(limit)
        )
        result = await self._session.execute(query)
        user_words = result.unique().scalars().all()

        items = []
        for uw in user_words:
            translation = next(
                (t for t in uw.word.translations if t.target_language == target_language),
                None,
            )
            if translation:
                items.append(
                    UserWordWithDetailsDTO(
                        id=uw.id,
                        user_id=uw.user_id,
                        word=WordWithTranslationDTO(
                            id=uw.word.id,
                            text=uw.word.text,
                            language=uw.word.language,
                            phonetic=uw.word.phonetic,
                            audio_url=uw.word.audio_url,
                            translation=translation.translated_text,
                            example_sentence=translation.example_sentence,
                        ),
                        added_at=uw.added_at,
                        is_learned=uw.is_learned,
                    )
                )

        return items

    async def count_user_words(self, user_id: UUID) -> int:
        query = select(func.count()).where(self._model.user_id == user_id)
        result = await self._session.execute(query)
        return result.scalar_one()

    async def count_unlearned_by_source_language(
        self,
        user_id: UUID,
    ) -> dict[Language, int]:
        """Count unlearned words grouped by source language."""
        query = (
            select(Word.language, func.count())
            .join(self._model, self._model.word_id == Word.id)
            .where(
                self._model.user_id == user_id,
                self._model.is_learned == False,  # noqa: E712
            )
            .group_by(Word.language)
        )
        result = await self._session.execute(query)
        return {row[0]: row[1] for row in result.all()}

    async def count_unlearned_for_language(
        self,
        user_id: UUID,
        source_language: Language,
    ) -> int:
        """Count unlearned words for a specific source language."""
        query = (
            select(func.count())
            .select_from(self._model)
            .join(Word, self._model.word_id == Word.id)
            .where(
                self._model.user_id == user_id,
                self._model.is_learned == False,  # noqa: E712
                Word.language == source_language,
            )
        )
        result = await self._session.execute(query)
        return result.scalar_one()

    async def get_stats_by_language(
        self,
        user_id: UUID,
    ) -> dict[Language, tuple[int, int]]:
        """Get (learned, total) counts per language."""
        query = (
            select(
                Word.language,
                func.sum(case((self._model.is_learned == True, 1), else_=0)),  # noqa: E712
                func.count(),
            )
            .join(self._model, self._model.word_id == Word.id)
            .where(self._model.user_id == user_id)
            .group_by(Word.language)
        )
        result = await self._session.execute(query)
        return {lang: (int(learned), int(total)) for lang, learned, total in result.all()}

    async def mark_as_learned(self, user_word_id: UUID) -> None:
        query = select(self._model).where(self._model.id == user_word_id)
        result = await self._session.execute(query)
        user_word = result.scalar_one_or_none()
        if user_word:
            user_word.is_learned = True
            await self._session.flush()

    async def delete_by_id(self, user_word_id: UUID) -> None:
        query = delete(self._model).where(self._model.id == user_word_id)
        await self._session.execute(query)
        await self._session.flush()


class UserWordListRepository(BaseRepository[UserWordList, UserWordListCreateDTO, UserWordListReadDTO]):
    _model = UserWordList
    _create_dto = UserWordListCreateDTO
    _read_dto = UserWordListReadDTO

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_user_added_lists(self, user_id: UUID) -> set[str]:
        """Get IDs of all word lists the user has added."""
        query = select(self._model.word_list_id).where(self._model.user_id == user_id)
        result = await self._session.execute(query)
        return {row[0] for row in result.all()}

    async def is_list_added(self, user_id: UUID, word_list_id: str) -> bool:
        """Check if a specific list was added by user."""
        query = select(func.count()).where(
            self._model.user_id == user_id,
            self._model.word_list_id == word_list_id,
        )
        result = await self._session.execute(query)
        return result.scalar_one() > 0
