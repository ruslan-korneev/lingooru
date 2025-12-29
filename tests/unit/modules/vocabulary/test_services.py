import pytest

from src.core.exceptions import ConflictError
from src.modules.users.dto import UserReadDTO
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
