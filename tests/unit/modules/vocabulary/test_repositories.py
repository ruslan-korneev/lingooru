import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.users.dto import UserReadDTO
from src.modules.vocabulary.dto import (
    TranslationCreateDTO,
    UserWordCreateDTO,
    WordCreateDTO,
)
from src.modules.vocabulary.models import Language
from src.modules.vocabulary.repositories import (
    TranslationRepository,
    UserWordRepository,
    WordRepository,
)

# Test constants
WORD_TEXT_SAVE = "apple"
WORD_TEXT_LOOKUP = "banana"
WORD_TEXT_WITH_TRANSLATION = "cherry"
WORD_TEXT_NOT_FOUND = "nonexistent"
PAGINATION_TOTAL = 5
PAGINATION_LIMIT = 3


class TestWordRepository:
    async def test_save_word(
        self,
        word_repository: WordRepository,
    ) -> None:
        dto = WordCreateDTO(
            text=WORD_TEXT_SAVE,
            language=Language.EN,
            phonetic="/ˈæp.əl/",  # noqa: RUF001
        )

        result = await word_repository.save(dto)

        assert result.id is not None
        assert result.text == WORD_TEXT_SAVE
        assert result.language == Language.EN
        assert result.phonetic == "/ˈæp.əl/"  # noqa: RUF001

    async def test_get_by_text_and_language(
        self,
        word_repository: WordRepository,
    ) -> None:
        dto = WordCreateDTO(text=WORD_TEXT_LOOKUP, language=Language.EN)
        await word_repository.save(dto)

        result = await word_repository.get_by_text_and_language(
            WORD_TEXT_LOOKUP,
            Language.EN,
        )

        assert result is not None
        assert result.text == WORD_TEXT_LOOKUP
        assert result.language == Language.EN

    async def test_get_by_text_and_language_not_found(
        self,
        word_repository: WordRepository,
    ) -> None:
        result = await word_repository.get_by_text_and_language(
            WORD_TEXT_NOT_FOUND,
            Language.EN,
        )

        assert result is None

    async def test_get_by_text_and_language_wrong_language(
        self,
        word_repository: WordRepository,
    ) -> None:
        dto = WordCreateDTO(text="unique_word", language=Language.EN)
        await word_repository.save(dto)

        result = await word_repository.get_by_text_and_language(
            "unique_word",
            Language.KO,
        )

        assert result is None

    async def test_get_by_id(
        self,
        word_repository: WordRepository,
    ) -> None:
        dto = WordCreateDTO(text="get_by_id_word", language=Language.EN)
        saved = await word_repository.save(dto)

        result = await word_repository.get_by_id(saved.id)

        assert result is not None
        assert result.id == saved.id
        assert result.text == "get_by_id_word"

    async def test_get_by_id_not_found(
        self,
        word_repository: WordRepository,
    ) -> None:
        result = await word_repository.get_by_id(uuid.uuid4())

        assert result is None

    async def test_get_with_translation(
        self,
        session: AsyncSession,
        word_repository: WordRepository,
        translation_repository: TranslationRepository,
    ) -> None:
        word_dto = WordCreateDTO(
            text=WORD_TEXT_WITH_TRANSLATION,
            language=Language.EN,
            phonetic="/ˈtʃer.i/",  # noqa: RUF001
        )
        word = await word_repository.save(word_dto)

        trans_dto = TranslationCreateDTO(
            word_id=word.id,
            translated_text="вишня",
            target_language=Language.RU,
            example_sentence="I love cherries.",
        )
        await translation_repository.save(trans_dto)
        await session.flush()

        result = await word_repository.get_with_translation(word.id, Language.RU)

        assert result is not None
        assert result.text == WORD_TEXT_WITH_TRANSLATION
        assert result.translation == "вишня"
        assert result.example_sentence == "I love cherries."

    async def test_get_with_translation_not_found(
        self,
        word_repository: WordRepository,
    ) -> None:
        dto = WordCreateDTO(text="no_translation", language=Language.EN)
        word = await word_repository.save(dto)

        result = await word_repository.get_with_translation(word.id, Language.RU)

        assert result is None


class TestTranslationRepository:
    async def test_save_translation(
        self,
        session: AsyncSession,
        word_repository: WordRepository,
        translation_repository: TranslationRepository,
    ) -> None:
        word_dto = WordCreateDTO(text="test_word", language=Language.EN)
        word = await word_repository.save(word_dto)
        await session.flush()

        trans_dto = TranslationCreateDTO(
            word_id=word.id,
            translated_text="тестовое слово",
            target_language=Language.RU,
        )

        result = await translation_repository.save(trans_dto)

        assert result.id is not None
        assert result.word_id == word.id
        assert result.translated_text == "тестовое слово"
        assert result.target_language == Language.RU

    async def test_get_by_word_and_language(
        self,
        session: AsyncSession,
        word_repository: WordRepository,
        translation_repository: TranslationRepository,
    ) -> None:
        word_dto = WordCreateDTO(text="lookup_word", language=Language.EN)
        word = await word_repository.save(word_dto)
        await session.flush()

        trans_dto = TranslationCreateDTO(
            word_id=word.id,
            translated_text="слово для поиска",
            target_language=Language.RU,
        )
        await translation_repository.save(trans_dto)
        await session.flush()

        result = await translation_repository.get_by_word_and_language(
            word.id,
            Language.RU,
        )

        assert result is not None
        assert result.word_id == word.id
        assert result.target_language == Language.RU

    async def test_get_by_word_and_language_not_found(
        self,
        translation_repository: TranslationRepository,
    ) -> None:
        result = await translation_repository.get_by_word_and_language(
            uuid.uuid4(),
            Language.RU,
        )

        assert result is None


class TestUserWordRepository:
    async def test_get_by_user_and_word(
        self,
        session: AsyncSession,
        sample_user: UserReadDTO,
        word_repository: WordRepository,
        user_word_repository: UserWordRepository,
    ) -> None:
        word_dto = WordCreateDTO(text="user_word_test", language=Language.EN)
        word = await word_repository.save(word_dto)
        await session.flush()

        user_word_dto = UserWordCreateDTO(
            user_id=sample_user.id,
            word_id=word.id,
        )
        saved = await user_word_repository.save(user_word_dto)
        await session.flush()

        result = await user_word_repository.get_by_user_and_word(
            sample_user.id,
            word.id,
        )

        assert result is not None
        assert result.id == saved.id
        assert result.user_id == sample_user.id
        assert result.word_id == word.id
        assert result.is_learned is False

    async def test_get_by_user_and_word_not_found(
        self,
        sample_user: UserReadDTO,
        user_word_repository: UserWordRepository,
    ) -> None:
        result = await user_word_repository.get_by_user_and_word(
            sample_user.id,
            uuid.uuid4(),
        )

        assert result is None

    async def test_mark_as_learned(
        self,
        session: AsyncSession,
        sample_user: UserReadDTO,
        word_repository: WordRepository,
        user_word_repository: UserWordRepository,
    ) -> None:
        word_dto = WordCreateDTO(text="learn_test", language=Language.EN)
        word = await word_repository.save(word_dto)
        await session.flush()

        user_word_dto = UserWordCreateDTO(
            user_id=sample_user.id,
            word_id=word.id,
        )
        saved = await user_word_repository.save(user_word_dto)
        await session.flush()

        await user_word_repository.mark_as_learned(saved.id)

        result = await user_word_repository.get_by_user_and_word(
            sample_user.id,
            word.id,
        )

        assert result is not None
        assert result.is_learned is True

    async def test_count_user_words(
        self,
        session: AsyncSession,
        sample_user: UserReadDTO,
        word_repository: WordRepository,
        user_word_repository: UserWordRepository,
    ) -> None:
        for i in range(PAGINATION_TOTAL):
            word_dto = WordCreateDTO(text=f"count_word_{i}", language=Language.EN)
            word = await word_repository.save(word_dto)
            await session.flush()

            user_word_dto = UserWordCreateDTO(
                user_id=sample_user.id,
                word_id=word.id,
            )
            await user_word_repository.save(user_word_dto)
            await session.flush()

        count = await user_word_repository.count_user_words(sample_user.id)

        assert count == PAGINATION_TOTAL

    async def test_delete_by_id(
        self,
        session: AsyncSession,
        sample_user: UserReadDTO,
        word_repository: WordRepository,
        user_word_repository: UserWordRepository,
    ) -> None:
        word_dto = WordCreateDTO(text="delete_test", language=Language.EN)
        word = await word_repository.save(word_dto)
        await session.flush()

        user_word_dto = UserWordCreateDTO(
            user_id=sample_user.id,
            word_id=word.id,
        )
        saved = await user_word_repository.save(user_word_dto)
        await session.flush()

        await user_word_repository.delete_by_id(saved.id)

        result = await user_word_repository.get_by_user_and_word(
            sample_user.id,
            word.id,
        )

        assert result is None

    async def test_get_words_for_learning(
        self,
        session: AsyncSession,
        sample_user: UserReadDTO,
        word_repository: WordRepository,
        translation_repository: TranslationRepository,
        user_word_repository: UserWordRepository,
    ) -> None:
        for i in range(PAGINATION_TOTAL):
            word_dto = WordCreateDTO(text=f"learning_word_{i}", language=Language.EN)
            word = await word_repository.save(word_dto)
            await session.flush()

            trans_dto = TranslationCreateDTO(
                word_id=word.id,
                translated_text=f"слово_{i}",
                target_language=Language.RU,
            )
            await translation_repository.save(trans_dto)
            await session.flush()

            user_word_dto = UserWordCreateDTO(
                user_id=sample_user.id,
                word_id=word.id,
            )
            await user_word_repository.save(user_word_dto)
            await session.flush()

        result = await user_word_repository.get_words_for_learning(
            user_id=sample_user.id,
            target_language=Language.RU,
            limit=PAGINATION_LIMIT,
        )

        assert len(result) == PAGINATION_LIMIT
        assert all(not item.is_learned for item in result)

    async def test_get_user_vocabulary_paginated(
        self,
        session: AsyncSession,
        sample_user: UserReadDTO,
        word_repository: WordRepository,
        translation_repository: TranslationRepository,
        user_word_repository: UserWordRepository,
    ) -> None:
        for i in range(PAGINATION_TOTAL):
            word_dto = WordCreateDTO(text=f"vocab_word_{i}", language=Language.EN)
            word = await word_repository.save(word_dto)
            await session.flush()

            trans_dto = TranslationCreateDTO(
                word_id=word.id,
                translated_text=f"словарное_слово_{i}",
                target_language=Language.RU,
            )
            await translation_repository.save(trans_dto)
            await session.flush()

            user_word_dto = UserWordCreateDTO(
                user_id=sample_user.id,
                word_id=word.id,
            )
            await user_word_repository.save(user_word_dto)
            await session.flush()

        result = await user_word_repository.get_user_vocabulary_paginated(
            user_id=sample_user.id,
            target_language=Language.RU,
            limit=PAGINATION_LIMIT,
            offset=0,
        )

        assert len(result.items) == PAGINATION_LIMIT
        assert result.total == PAGINATION_TOTAL

    async def test_get_words_for_learning_with_source_language_filter(
        self,
        session: AsyncSession,
        sample_user: UserReadDTO,
        word_repository: WordRepository,
        translation_repository: TranslationRepository,
        user_word_repository: UserWordRepository,
    ) -> None:
        # Add English words
        for i in range(3):
            word_dto = WordCreateDTO(text=f"english_word_{i}", language=Language.EN)
            word = await word_repository.save(word_dto)
            await session.flush()

            trans_dto = TranslationCreateDTO(
                word_id=word.id,
                translated_text=f"англ_{i}",
                target_language=Language.RU,
            )
            await translation_repository.save(trans_dto)
            await session.flush()

            user_word_dto = UserWordCreateDTO(
                user_id=sample_user.id,
                word_id=word.id,
            )
            await user_word_repository.save(user_word_dto)
            await session.flush()

        # Add Korean words
        for i in range(2):
            word_dto = WordCreateDTO(text=f"korean_word_{i}", language=Language.KO)
            word = await word_repository.save(word_dto)
            await session.flush()

            trans_dto = TranslationCreateDTO(
                word_id=word.id,
                translated_text=f"корейский_{i}",
                target_language=Language.RU,
            )
            await translation_repository.save(trans_dto)
            await session.flush()

            user_word_dto = UserWordCreateDTO(
                user_id=sample_user.id,
                word_id=word.id,
            )
            await user_word_repository.save(user_word_dto)
            await session.flush()

        # Test filter by English
        en_result = await user_word_repository.get_words_for_learning(
            user_id=sample_user.id,
            target_language=Language.RU,
            source_language=Language.EN,
            limit=10,
        )
        assert len(en_result) == 3  # noqa: PLR2004
        assert all(item.word.language == Language.EN for item in en_result)

        # Test filter by Korean
        ko_result = await user_word_repository.get_words_for_learning(
            user_id=sample_user.id,
            target_language=Language.RU,
            source_language=Language.KO,
            limit=10,
        )
        assert len(ko_result) == 2  # noqa: PLR2004
        assert all(item.word.language == Language.KO for item in ko_result)

        # Test no filter (all languages)
        all_result = await user_word_repository.get_words_for_learning(
            user_id=sample_user.id,
            target_language=Language.RU,
            limit=10,
        )
        assert len(all_result) == 5  # noqa: PLR2004

    async def test_count_unlearned_by_source_language(
        self,
        session: AsyncSession,
        sample_user: UserReadDTO,
        word_repository: WordRepository,
        translation_repository: TranslationRepository,
        user_word_repository: UserWordRepository,
    ) -> None:
        # Add 3 English words (1 learned, 2 unlearned)
        en_user_words = []
        for i in range(3):
            word_dto = WordCreateDTO(text=f"count_en_{i}", language=Language.EN)
            word = await word_repository.save(word_dto)
            await session.flush()

            trans_dto = TranslationCreateDTO(
                word_id=word.id,
                translated_text=f"счет_англ_{i}",
                target_language=Language.RU,
            )
            await translation_repository.save(trans_dto)
            await session.flush()

            user_word_dto = UserWordCreateDTO(
                user_id=sample_user.id,
                word_id=word.id,
            )
            saved = await user_word_repository.save(user_word_dto)
            en_user_words.append(saved)
            await session.flush()

        # Mark one English word as learned
        await user_word_repository.mark_as_learned(en_user_words[0].id)
        await session.flush()

        # Add 2 Korean words (all unlearned)
        for i in range(2):
            word_dto = WordCreateDTO(text=f"count_ko_{i}", language=Language.KO)
            word = await word_repository.save(word_dto)
            await session.flush()

            trans_dto = TranslationCreateDTO(
                word_id=word.id,
                translated_text=f"счет_корейский_{i}",
                target_language=Language.RU,
            )
            await translation_repository.save(trans_dto)
            await session.flush()

            user_word_dto = UserWordCreateDTO(
                user_id=sample_user.id,
                word_id=word.id,
            )
            await user_word_repository.save(user_word_dto)
            await session.flush()

        counts = await user_word_repository.count_unlearned_by_source_language(sample_user.id)

        assert counts[Language.EN] == 2  # noqa: PLR2004 - 3 - 1 learned
        assert counts[Language.KO] == 2  # noqa: PLR2004

    async def test_count_unlearned_for_language(
        self,
        session: AsyncSession,
        sample_user: UserReadDTO,
        word_repository: WordRepository,
        translation_repository: TranslationRepository,
        user_word_repository: UserWordRepository,
    ) -> None:
        # Add 3 English words (1 learned, 2 unlearned)
        en_user_words = []
        for i in range(3):
            word_dto = WordCreateDTO(text=f"single_count_en_{i}", language=Language.EN)
            word = await word_repository.save(word_dto)
            await session.flush()

            trans_dto = TranslationCreateDTO(
                word_id=word.id,
                translated_text=f"одиночный_англ_{i}",
                target_language=Language.RU,
            )
            await translation_repository.save(trans_dto)
            await session.flush()

            user_word_dto = UserWordCreateDTO(
                user_id=sample_user.id,
                word_id=word.id,
            )
            saved = await user_word_repository.save(user_word_dto)
            en_user_words.append(saved)
            await session.flush()

        # Mark one English word as learned
        await user_word_repository.mark_as_learned(en_user_words[0].id)
        await session.flush()

        # Add 2 Korean words (all unlearned)
        for i in range(2):
            word_dto = WordCreateDTO(text=f"single_count_ko_{i}", language=Language.KO)
            word = await word_repository.save(word_dto)
            await session.flush()

            trans_dto = TranslationCreateDTO(
                word_id=word.id,
                translated_text=f"одиночный_корейский_{i}",
                target_language=Language.RU,
            )
            await translation_repository.save(trans_dto)
            await session.flush()

            user_word_dto = UserWordCreateDTO(
                user_id=sample_user.id,
                word_id=word.id,
            )
            await user_word_repository.save(user_word_dto)
            await session.flush()

        # Test count for specific language
        expected_en_unlearned = 2  # 3 - 1 learned
        en_count = await user_word_repository.count_unlearned_for_language(sample_user.id, Language.EN)
        assert en_count == expected_en_unlearned

        expected_ko_unlearned = 2
        ko_count = await user_word_repository.count_unlearned_for_language(sample_user.id, Language.KO)
        assert ko_count == expected_ko_unlearned

        # Test count for language with no words
        ru_count = await user_word_repository.count_unlearned_for_language(sample_user.id, Language.RU)
        assert ru_count == 0

    async def test_get_stats_by_language(
        self,
        session: AsyncSession,
        sample_user: UserReadDTO,
        word_repository: WordRepository,
        translation_repository: TranslationRepository,
        user_word_repository: UserWordRepository,
    ) -> None:
        # Add 4 English words (2 learned, 2 unlearned)
        en_user_words = []
        for i in range(4):
            word_dto = WordCreateDTO(text=f"stats_en_{i}", language=Language.EN)
            word = await word_repository.save(word_dto)
            await session.flush()

            trans_dto = TranslationCreateDTO(
                word_id=word.id,
                translated_text=f"статистика_англ_{i}",
                target_language=Language.RU,
            )
            await translation_repository.save(trans_dto)
            await session.flush()

            user_word_dto = UserWordCreateDTO(
                user_id=sample_user.id,
                word_id=word.id,
            )
            saved = await user_word_repository.save(user_word_dto)
            en_user_words.append(saved)
            await session.flush()

        # Mark 2 English words as learned
        await user_word_repository.mark_as_learned(en_user_words[0].id)
        await user_word_repository.mark_as_learned(en_user_words[1].id)
        await session.flush()

        # Add 3 Korean words (1 learned, 2 unlearned)
        ko_user_words = []
        for i in range(3):
            word_dto = WordCreateDTO(text=f"stats_ko_{i}", language=Language.KO)
            word = await word_repository.save(word_dto)
            await session.flush()

            trans_dto = TranslationCreateDTO(
                word_id=word.id,
                translated_text=f"статистика_корейский_{i}",
                target_language=Language.RU,
            )
            await translation_repository.save(trans_dto)
            await session.flush()

            user_word_dto = UserWordCreateDTO(
                user_id=sample_user.id,
                word_id=word.id,
            )
            saved = await user_word_repository.save(user_word_dto)
            ko_user_words.append(saved)
            await session.flush()

        # Mark 1 Korean word as learned
        await user_word_repository.mark_as_learned(ko_user_words[0].id)
        await session.flush()

        stats = await user_word_repository.get_stats_by_language(sample_user.id)

        assert stats[Language.EN] == (2, 4)  # 2 learned out of 4
        assert stats[Language.KO] == (1, 3)  # 1 learned out of 3

    async def test_get_user_vocabulary_paginated_with_source_language_filter(
        self,
        session: AsyncSession,
        sample_user: UserReadDTO,
        word_repository: WordRepository,
        translation_repository: TranslationRepository,
        user_word_repository: UserWordRepository,
    ) -> None:
        # Add English words
        for i in range(3):
            word_dto = WordCreateDTO(text=f"filter_en_{i}", language=Language.EN)
            word = await word_repository.save(word_dto)
            await session.flush()

            trans_dto = TranslationCreateDTO(
                word_id=word.id,
                translated_text=f"фильтр_англ_{i}",
                target_language=Language.RU,
            )
            await translation_repository.save(trans_dto)
            await session.flush()

            user_word_dto = UserWordCreateDTO(
                user_id=sample_user.id,
                word_id=word.id,
            )
            await user_word_repository.save(user_word_dto)
            await session.flush()

        # Add Korean words
        for i in range(2):
            word_dto = WordCreateDTO(text=f"filter_ko_{i}", language=Language.KO)
            word = await word_repository.save(word_dto)
            await session.flush()

            trans_dto = TranslationCreateDTO(
                word_id=word.id,
                translated_text=f"фильтр_корейский_{i}",
                target_language=Language.RU,
            )
            await translation_repository.save(trans_dto)
            await session.flush()

            user_word_dto = UserWordCreateDTO(
                user_id=sample_user.id,
                word_id=word.id,
            )
            await user_word_repository.save(user_word_dto)
            await session.flush()

        # Test filter by English
        en_result = await user_word_repository.get_user_vocabulary_paginated(
            user_id=sample_user.id,
            target_language=Language.RU,
            source_language=Language.EN,
            limit=10,
            offset=0,
        )
        assert len(en_result.items) == 3  # noqa: PLR2004
        assert en_result.total == 3  # noqa: PLR2004
        assert all(item.word.language == Language.EN for item in en_result.items)

        # Test filter by Korean
        ko_result = await user_word_repository.get_user_vocabulary_paginated(
            user_id=sample_user.id,
            target_language=Language.RU,
            source_language=Language.KO,
            limit=10,
            offset=0,
        )
        assert len(ko_result.items) == 2  # noqa: PLR2004
        assert ko_result.total == 2  # noqa: PLR2004
        assert all(item.word.language == Language.KO for item in ko_result.items)

        # Test no filter (all languages)
        all_result = await user_word_repository.get_user_vocabulary_paginated(
            user_id=sample_user.id,
            target_language=Language.RU,
            limit=10,
            offset=0,
        )
        assert len(all_result.items) == 5  # noqa: PLR2004
        assert all_result.total == 5  # noqa: PLR2004
