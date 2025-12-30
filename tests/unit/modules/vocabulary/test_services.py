from unittest.mock import AsyncMock, patch

import pytest

from src.core.exceptions import ConflictError
from src.modules.users.dto import UserReadDTO
from src.modules.vocabulary.dictionary_client import DictionaryResult
from src.modules.vocabulary.dto import ManualWordInputDTO
from src.modules.vocabulary.models import Language
from src.modules.vocabulary.services import VocabularyService

# Test constants
WORD_ADD = "test_add"
WORD_DUPLICATE = "duplicate_word"
WORD_LOOKUP = "lookup_word"
WORD_LEARN = "learn_word"
WORD_COUNT = "count_word"
VOCAB_LIMIT = 5
VOCAB_OFFSET = 0
PAGINATION_LIMIT = 3


class TestVocabularyService:
    async def test_add_word_with_translation(
        self,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
    ) -> None:
        result = await vocabulary_service.add_word_with_translation(
            user_id=sample_user.id,
            text=WORD_ADD,
            translation="тестовое добавление",
            source_language=Language.EN,
            target_language=Language.RU,
            example_sentence="This is a test.",
            phonetic="/test/",
        )

        assert result.user_id == sample_user.id
        assert result.word.text == WORD_ADD
        assert result.word.translation == "тестовое добавление"
        assert result.word.phonetic == "/test/"
        assert result.word.example_sentence == "This is a test."
        assert result.is_learned is False

    async def test_add_word_with_translation_raises_conflict_for_duplicate(
        self,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
    ) -> None:
        await vocabulary_service.add_word_with_translation(
            user_id=sample_user.id,
            text=WORD_DUPLICATE,
            translation="дубликат",
            source_language=Language.EN,
            target_language=Language.RU,
        )

        with pytest.raises(ConflictError):
            await vocabulary_service.add_word_with_translation(
                user_id=sample_user.id,
                text=WORD_DUPLICATE,
                translation="другой перевод",
                source_language=Language.EN,
                target_language=Language.RU,
            )

    async def test_add_word_normalizes_text(
        self,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
    ) -> None:
        result = await vocabulary_service.add_word_with_translation(
            user_id=sample_user.id,
            text="  UPPERCASE  ",
            translation="верхний регистр",
            source_language=Language.EN,
            target_language=Language.RU,
        )

        assert result.word.text == "uppercase"

    async def test_get_user_vocabulary(
        self,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
    ) -> None:
        for i in range(VOCAB_LIMIT):
            await vocabulary_service.add_word_with_translation(
                user_id=sample_user.id,
                text=f"vocab_{i}",
                translation=f"словарь_{i}",
                source_language=Language.EN,
                target_language=Language.RU,
            )

        result = await vocabulary_service.get_user_vocabulary(
            user_id=sample_user.id,
            target_language=Language.RU,
            limit=PAGINATION_LIMIT,
            offset=VOCAB_OFFSET,
        )

        assert len(result.items) == PAGINATION_LIMIT
        assert result.total == VOCAB_LIMIT

    async def test_get_words_for_learning(
        self,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
    ) -> None:
        for i in range(VOCAB_LIMIT):
            await vocabulary_service.add_word_with_translation(
                user_id=sample_user.id,
                text=f"learning_{i}",
                translation=f"изучение_{i}",
                source_language=Language.EN,
                target_language=Language.RU,
            )

        result = await vocabulary_service.get_words_for_learning(
            user_id=sample_user.id,
            target_language=Language.RU,
            limit=PAGINATION_LIMIT,
        )

        assert len(result) == PAGINATION_LIMIT
        assert all(not word.is_learned for word in result)

    async def test_mark_word_learned(
        self,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
    ) -> None:
        user_word = await vocabulary_service.add_word_with_translation(
            user_id=sample_user.id,
            text=WORD_LEARN,
            translation="изучить",
            source_language=Language.EN,
            target_language=Language.RU,
        )

        await vocabulary_service.mark_word_learned(user_word.id)

        result = await vocabulary_service.get_words_for_learning(
            user_id=sample_user.id,
            target_language=Language.RU,
            limit=10,
        )

        word_ids = [w.id for w in result]
        assert user_word.id not in word_ids

    async def test_remove_word_from_vocabulary(
        self,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
    ) -> None:
        user_word = await vocabulary_service.add_word_with_translation(
            user_id=sample_user.id,
            text="remove_test",
            translation="удалить",
            source_language=Language.EN,
            target_language=Language.RU,
        )

        await vocabulary_service.remove_word_from_vocabulary(user_word.id)

        count = await vocabulary_service.count_user_words(sample_user.id)
        assert count == 0

    async def test_count_user_words(
        self,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
    ) -> None:
        for i in range(VOCAB_LIMIT):
            await vocabulary_service.add_word_with_translation(
                user_id=sample_user.id,
                text=f"{WORD_COUNT}_{i}",
                translation=f"счет_{i}",
                source_language=Language.EN,
                target_language=Language.RU,
            )

        count = await vocabulary_service.count_user_words(sample_user.id)

        assert count == VOCAB_LIMIT

    async def test_lookup_word_returns_none_for_nonexistent(
        self,
        vocabulary_service: VocabularyService,
    ) -> None:
        result = await vocabulary_service.lookup_word(
            text="nonexistent_word_xyz",
            source_language=Language.KO,
            target_language=Language.RU,
        )

        assert result is None

    async def test_different_users_can_have_same_word(
        self,
        sample_user: UserReadDTO,
        second_sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
    ) -> None:
        await vocabulary_service.add_word_with_translation(
            user_id=sample_user.id,
            text="shared_word",
            translation="общее слово",
            source_language=Language.EN,
            target_language=Language.RU,
        )

        result = await vocabulary_service.add_word_with_translation(
            user_id=second_sample_user.id,
            text="shared_word",
            translation="общее слово",
            source_language=Language.EN,
            target_language=Language.RU,
        )

        assert result.user_id == second_sample_user.id
        assert result.word.text == "shared_word"

    async def test_lookup_word_returns_existing_word_with_translation(
        self,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
    ) -> None:
        """Test lookup_word returns existing word when it has a translation."""
        # First add a word with translation
        await vocabulary_service.add_word_with_translation(
            user_id=sample_user.id,
            text="existing_lookup",
            translation="существующий",
            source_language=Language.EN,
            target_language=Language.RU,
        )

        # Now lookup should return the word
        result = await vocabulary_service.lookup_word(
            text="existing_lookup",
            source_language=Language.EN,
            target_language=Language.RU,
        )

        assert result is not None
        assert result.text == "existing_lookup"
        assert result.translation == "существующий"

    async def test_lookup_word_english_calls_api_when_not_in_db(
        self,
        vocabulary_service: VocabularyService,
    ) -> None:
        """Test lookup_word calls dictionary API for English words not in DB."""
        mock_result = DictionaryResult(
            word="hello",
            phonetic="/helo/",
            audio_url="https://example.com/audio.mp3",
            definition="greeting",
            example="Hello, world!",
        )

        with patch.object(
            vocabulary_service._dict_client,  # noqa: SLF001
            "lookup",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await vocabulary_service.lookup_word(
                text="hello",
                source_language=Language.EN,
                target_language=Language.RU,
            )

        # Returns None because API doesn't provide RU translation
        assert result is None

    async def test_lookup_word_english_api_not_found(
        self,
        vocabulary_service: VocabularyService,
    ) -> None:
        """Test lookup_word returns None when API doesn't find the word."""
        with patch.object(
            vocabulary_service._dict_client,  # noqa: SLF001
            "lookup",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await vocabulary_service.lookup_word(
                text="nonexistent_api_word",
                source_language=Language.EN,
                target_language=Language.RU,
            )

        assert result is None

    async def test_lookup_word_existing_word_no_translation(
        self,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
    ) -> None:
        """Test lookup_word when word exists but has no translation for target language."""
        # Add a word with RU translation
        await vocabulary_service.add_word_with_translation(
            user_id=sample_user.id,
            text="partial_word",
            translation="частичное",
            source_language=Language.EN,
            target_language=Language.RU,
        )

        # Lookup with different target language (no translation exists)
        result = await vocabulary_service.lookup_word(
            text="partial_word",
            source_language=Language.EN,
            target_language=Language.KO,  # No KO translation
        )

        assert result is None

    async def test_add_word_updates_existing_word_with_phonetic(
        self,
        sample_user: UserReadDTO,
        second_sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
    ) -> None:
        """Test adding word when it exists triggers phonetic update branch."""
        # First user adds word without phonetic
        await vocabulary_service.add_word_with_translation(
            user_id=sample_user.id,
            text="update_phonetic_word",
            translation="обновить",
            source_language=Language.EN,
            target_language=Language.RU,
        )

        # Second user adds same word with phonetic - this triggers lines 109-113
        result = await vocabulary_service.add_word_with_translation(
            user_id=second_sample_user.id,
            text="update_phonetic_word",
            translation="обновить",
            source_language=Language.EN,
            target_language=Language.RU,
            phonetic="/update/",
            audio_url="https://example.com/audio.mp3",
        )

        assert result.user_id == second_sample_user.id

    async def test_add_word_manual(
        self,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
    ) -> None:
        """Test add_word_manual creates word from ManualWordInputDTO."""
        dto = ManualWordInputDTO(
            text="manual_word",
            translation="ручной ввод",
            example_sentence="This is manual.",
        )

        result = await vocabulary_service.add_word_manual(
            user_id=sample_user.id,
            dto=dto,
            source_language=Language.EN,
            target_language=Language.RU,
        )

        assert result.word.text == "manual_word"
        assert result.word.translation == "ручной ввод"
        assert result.word.example_sentence == "This is manual."

    async def test_get_unlearned_counts_by_language(
        self,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
    ) -> None:
        """Test counting unlearned words grouped by language."""
        # Add EN words
        for i in range(3):
            await vocabulary_service.add_word_with_translation(
                user_id=sample_user.id,
                text=f"en_word_{i}",
                translation=f"слово_{i}",
                source_language=Language.EN,
                target_language=Language.RU,
            )

        # Add KO words
        for i in range(2):
            await vocabulary_service.add_word_with_translation(
                user_id=sample_user.id,
                text=f"ko_word_{i}",
                translation=f"한국어_{i}",
                source_language=Language.KO,
                target_language=Language.RU,
            )

        counts = await vocabulary_service.get_unlearned_counts_by_language(sample_user.id)

        assert counts.get(Language.EN) == 3  # noqa: PLR2004
        assert counts.get(Language.KO) == 2  # noqa: PLR2004

    async def test_count_unlearned_for_language(
        self,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
    ) -> None:
        """Test counting unlearned words for specific language."""
        for i in range(4):
            await vocabulary_service.add_word_with_translation(
                user_id=sample_user.id,
                text=f"count_lang_{i}",
                translation=f"счет_{i}",
                source_language=Language.EN,
                target_language=Language.RU,
            )

        count = await vocabulary_service.count_unlearned_for_language(sample_user.id, Language.EN)

        assert count == 4  # noqa: PLR2004

    async def test_get_stats_by_language(
        self,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
    ) -> None:
        """Test getting (learned, total) stats per language."""
        # Add words
        for i in range(3):
            user_word = await vocabulary_service.add_word_with_translation(
                user_id=sample_user.id,
                text=f"stats_word_{i}",
                translation=f"статистика_{i}",
                source_language=Language.EN,
                target_language=Language.RU,
            )
            # Mark first word as learned
            if i == 0:
                await vocabulary_service.mark_word_learned(user_word.id)

        stats = await vocabulary_service.get_stats_by_language(sample_user.id)

        assert Language.EN in stats
        learned, total = stats[Language.EN]
        assert learned == 1
        assert total == 3  # noqa: PLR2004


class TestWordListMethods:
    """Tests for word list tracking methods."""

    async def test_mark_and_check_word_list_added(
        self,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
    ) -> None:
        """Test marking and checking if word list was added."""
        word_list_id = "basic_100"

        # Initially not added
        is_added = await vocabulary_service.is_word_list_added(sample_user.id, word_list_id)
        assert is_added is False

        # Mark as added
        await vocabulary_service.mark_word_list_added(
            user_id=sample_user.id,
            word_list_id=word_list_id,
            words_added=50,
        )

        # Now it should be added
        is_added = await vocabulary_service.is_word_list_added(sample_user.id, word_list_id)
        assert is_added is True

    async def test_get_user_added_word_lists(
        self,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
    ) -> None:
        """Test getting all word lists added by user."""
        # Add multiple word lists
        await vocabulary_service.mark_word_list_added(sample_user.id, "list_1", words_added=10)
        await vocabulary_service.mark_word_list_added(sample_user.id, "list_2", words_added=20)

        added_lists = await vocabulary_service.get_user_added_word_lists(sample_user.id)

        assert "list_1" in added_lists
        assert "list_2" in added_lists
        assert len(added_lists) == 2  # noqa: PLR2004
