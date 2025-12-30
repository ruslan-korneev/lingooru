from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError
from src.core.types.repositories import PaginatedResult
from src.modules.vocabulary.dictionary_client import (
    DictionaryResult,
    get_dictionary_client,
)
from src.modules.vocabulary.dto import (
    ManualWordInputDTO,
    TranslationCreateDTO,
    UserWordCreateDTO,
    UserWordListCreateDTO,
    UserWordWithDetailsDTO,
    WordCreateDTO,
    WordWithTranslationDTO,
)
from src.modules.vocabulary.enums import Language
from src.modules.vocabulary.repositories import (
    TranslationRepository,
    UserWordListRepository,
    UserWordRepository,
    WordRepository,
)


class VocabularyService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._word_repo = WordRepository(session)
        self._translation_repo = TranslationRepository(session)
        self._user_word_repo = UserWordRepository(session)
        self._user_word_list_repo = UserWordListRepository(session)
        self._dict_client = get_dictionary_client()

    async def lookup_word(
        self,
        text: str,
        source_language: Language,
        target_language: Language,
    ) -> WordWithTranslationDTO | None:
        """
        Look up a word. First check local DB, then external API.
        Returns None if not found (user should provide manual input).
        """
        text = text.lower().strip()

        # Check if word exists in local DB with translation
        existing_word = await self._word_repo.get_by_text_and_language(text, source_language)
        if existing_word:
            word_with_trans = await self._word_repo.get_with_translation(existing_word.id, target_language)
            if word_with_trans:
                return word_with_trans

        # If not in DB and source is English, try dictionary API
        if source_language is Language.EN:
            dict_result = await self._dict_client.lookup(text)
            if dict_result:
                # Store the word in DB (without translation - will be added later)
                await self._create_word_from_dict(dict_result, source_language)
                # Return None to prompt for translation since API doesn't provide RU translation
                return None

        return None

    async def _create_word_from_dict(
        self,
        result: DictionaryResult,
        language: Language,
    ) -> None:
        """Create a word from dictionary API result (without translation)."""
        existing = await self._word_repo.get_by_text_and_language(result.word, language)
        if existing:
            return

        dto = WordCreateDTO(
            text=result.word,
            language=language,
            phonetic=result.phonetic,
            audio_url=result.audio_url,
        )
        await self._word_repo.save(dto)

    async def add_word_with_translation(
        self,
        user_id: UUID,
        text: str,
        translation: str,
        source_language: Language,
        target_language: Language,
        example_sentence: str | None = None,
        phonetic: str | None = None,
        audio_url: str | None = None,
    ) -> UserWordWithDetailsDTO:
        """
        Add a word with translation to user's vocabulary.
        Creates Word and Translation if they don't exist.
        """
        text = text.lower().strip()

        # Get or create Word
        existing_word = await self._word_repo.get_by_text_and_language(text, source_language)
        if existing_word:
            word_id = existing_word.id
            # Update phonetic/audio if not set but we have new data
            if phonetic or audio_url:
                word_model = await self._word_repo.get_by_id(word_id)
                if word_model and (not word_model.phonetic or not word_model.audio_url):
                    # Could update here if needed
                    pass
        else:
            word_dto = WordCreateDTO(
                text=text,
                language=source_language,
                phonetic=phonetic,
                audio_url=audio_url,
            )
            word = await self._word_repo.save(word_dto)
            word_id = word.id

        # Get or create Translation
        existing_trans = await self._translation_repo.get_by_word_and_language(word_id, target_language)
        if not existing_trans:
            trans_dto = TranslationCreateDTO(
                word_id=word_id,
                translated_text=translation,
                target_language=target_language,
                example_sentence=example_sentence,
            )
            await self._translation_repo.save(trans_dto)

        # Check if user already has this word
        existing_user_word = await self._user_word_repo.get_by_user_and_word(user_id, word_id)
        if existing_user_word:
            raise ConflictError

        # Create UserWord
        user_word_dto = UserWordCreateDTO(user_id=user_id, word_id=word_id)
        user_word = await self._user_word_repo.save(user_word_dto)

        # Get full details
        word_with_trans = await self._word_repo.get_with_translation(word_id, target_language)
        if not word_with_trans:
            raise NotFoundError

        return UserWordWithDetailsDTO(
            id=user_word.id,
            user_id=user_id,
            word=word_with_trans,
            added_at=user_word.added_at,
            is_learned=user_word.is_learned,
        )

    async def add_word_manual(
        self,
        user_id: UUID,
        dto: ManualWordInputDTO,
        source_language: Language,
        target_language: Language,
    ) -> UserWordWithDetailsDTO:
        """Add a manually entered word to user's vocabulary."""
        return await self.add_word_with_translation(
            user_id=user_id,
            text=dto.text,
            translation=dto.translation,
            source_language=source_language,
            target_language=target_language,
            example_sentence=dto.example_sentence,
        )

    async def get_user_vocabulary(
        self,
        user_id: UUID,
        target_language: Language,
        limit: int = 10,
        offset: int = 0,
        learned_only: bool | None = None,
        source_language: Language | None = None,
    ) -> PaginatedResult[UserWordWithDetailsDTO]:
        """Get paginated user vocabulary."""
        return await self._user_word_repo.get_user_vocabulary_paginated(
            user_id=user_id,
            target_language=target_language,
            limit=limit,
            offset=offset,
            learned_only=learned_only,
            source_language=source_language,
        )

    async def get_words_for_learning(
        self,
        user_id: UUID,
        target_language: Language,
        source_language: Language | None = None,
        limit: int = 10,
    ) -> Sequence[UserWordWithDetailsDTO]:
        """Get unlearned words for learning session."""
        return await self._user_word_repo.get_words_for_learning(
            user_id=user_id,
            target_language=target_language,
            source_language=source_language,
            limit=limit,
        )

    async def mark_word_learned(self, user_word_id: UUID) -> None:
        """Mark a word as learned."""
        await self._user_word_repo.mark_as_learned(user_word_id)

    async def remove_word_from_vocabulary(self, user_word_id: UUID) -> None:
        """Remove a word from user's vocabulary."""
        await self._user_word_repo.delete_by_id(user_word_id)

    async def count_user_words(self, user_id: UUID) -> int:
        """Count total words in user's vocabulary."""
        return await self._user_word_repo.count_user_words(user_id)

    async def get_unlearned_counts_by_language(
        self,
        user_id: UUID,
    ) -> dict[Language, int]:
        """Get count of unlearned words grouped by source language."""
        return await self._user_word_repo.count_unlearned_by_source_language(user_id)

    async def count_unlearned_for_language(
        self,
        user_id: UUID,
        source_language: Language,
    ) -> int:
        """Count unlearned words for a specific source language."""
        return await self._user_word_repo.count_unlearned_for_language(user_id, source_language)

    async def get_stats_by_language(
        self,
        user_id: UUID,
    ) -> dict[Language, tuple[int, int]]:
        """Get (learned, total) counts per source language."""
        return await self._user_word_repo.get_stats_by_language(user_id)

    # Word List methods

    async def get_user_added_word_lists(self, user_id: UUID) -> set[str]:
        """Get IDs of word lists already added by user."""
        return await self._user_word_list_repo.get_user_added_lists(user_id)

    async def is_word_list_added(self, user_id: UUID, word_list_id: str) -> bool:
        """Check if user has already added a word list."""
        return await self._user_word_list_repo.is_list_added(user_id, word_list_id)

    async def mark_word_list_added(
        self,
        user_id: UUID,
        word_list_id: str,
        words_added: int,
    ) -> None:
        """Record that user has added a word list."""
        dto = UserWordListCreateDTO(
            user_id=user_id,
            word_list_id=word_list_id,
            words_added=words_added,
        )
        await self._user_word_list_repo.save(dto)
