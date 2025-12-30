"""Unit tests for Voice service."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.srs.services import SRSService
from src.modules.users.dto import UserReadDTO
from src.modules.vocabulary.enums import Language
from src.modules.vocabulary.services import VocabularyService
from src.modules.voice.openai_client import PronunciationEvaluation, TranscriptionResult
from src.modules.voice.services import VoiceService


class TestVoiceService:
    """Test cases for Voice service."""

    async def test_get_words_for_pronunciation_returns_empty_for_new_user(
        self,
        session: AsyncSession,
        sample_user: UserReadDTO,
    ) -> None:
        """Test that get_words_for_pronunciation returns empty for new user."""
        service = VoiceService(session)
        words = await service.get_words_for_pronunciation(
            user_id=sample_user.id,
            source_language=Language.EN,
        )
        assert len(words) == 0

    async def test_get_words_for_pronunciation_returns_only_learned_words(
        self,
        session: AsyncSession,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
        srs_service: SRSService,
    ) -> None:
        """Test that only learned words are returned for pronunciation."""
        # Add a learned word
        learned_word = await vocabulary_service.add_word_with_translation(
            user_id=sample_user.id,
            text="pronunciation_test",
            translation="тест произношения",
            source_language=Language.EN,
            target_language=Language.RU,
        )
        await vocabulary_service.mark_word_learned(learned_word.id)
        await srs_service.get_or_create_review(learned_word.id)

        # Add an unlearned word
        await vocabulary_service.add_word_with_translation(
            user_id=sample_user.id,
            text="unlearned_word",
            translation="невыученное слово",
            source_language=Language.EN,
            target_language=Language.RU,
        )
        await session.flush()

        service = VoiceService(session)
        words = await service.get_words_for_pronunciation(
            user_id=sample_user.id,
            source_language=Language.EN,
        )

        assert len(words) == 1
        assert words[0].text == "pronunciation_test"

    async def test_get_words_for_pronunciation_filters_by_language(
        self,
        session: AsyncSession,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
        srs_service: SRSService,
    ) -> None:
        """Test that words are filtered by source language."""
        # Add English word
        en_word = await vocabulary_service.add_word_with_translation(
            user_id=sample_user.id,
            text="english_word",
            translation="английское слово",
            source_language=Language.EN,
            target_language=Language.RU,
        )
        await vocabulary_service.mark_word_learned(en_word.id)
        await srs_service.get_or_create_review(en_word.id)
        await session.flush()

        service = VoiceService(session)

        # Should find English word
        en_words = await service.get_words_for_pronunciation(
            user_id=sample_user.id,
            source_language=Language.EN,
        )
        assert len(en_words) == 1
        assert en_words[0].language == "en"

        # Should not find Korean word
        ko_words = await service.get_words_for_pronunciation(
            user_id=sample_user.id,
            source_language=Language.KO,
        )
        assert len(ko_words) == 0

    @patch("src.modules.voice.services.get_openai_client")
    async def test_process_voice_message_saves_log(
        self,
        mock_get_client: AsyncMock,
        session: AsyncSession,
        sample_user: UserReadDTO,
        vocabulary_service: VocabularyService,
        srs_service: SRSService,
    ) -> None:
        """Test that process_voice_message saves pronunciation log."""
        # Setup mock
        mock_client = AsyncMock()
        mock_client.transcribe.return_value = TranscriptionResult(
            text="hello",
            duration_seconds=1.5,
        )
        mock_client.check_pronunciation.return_value = PronunciationEvaluation(
            rating=4,
            feedback="Good pronunciation!",
            is_correct=True,
        )
        mock_get_client.return_value = mock_client

        # Add and learn a word
        user_word = await vocabulary_service.add_word_with_translation(
            user_id=sample_user.id,
            text="hello",
            translation="привет",
            source_language=Language.EN,
            target_language=Language.RU,
            phonetic="/həˈloʊ/",  # noqa: RUF001
        )
        await vocabulary_service.mark_word_learned(user_word.id)
        await srs_service.get_or_create_review(user_word.id)
        await session.flush()

        service = VoiceService(session)
        log = await service.process_voice_message(
            user_id=sample_user.id,
            word_id=user_word.word.id,
            expected_text="hello",
            audio_bytes=b"fake_audio_data",
            language="en",
            phonetic="/həˈloʊ/",  # noqa: RUF001
        )
        await session.flush()

        assert log is not None
        assert log.transcribed_text == "hello"
        assert log.expected_text == "hello"
        assert log.rating == 4  # noqa: PLR2004
        assert log.feedback == "Good pronunciation!"
        assert log.audio_duration_seconds == 1.5  # noqa: PLR2004

    async def test_get_session_stats_calculates_correctly(
        self,
        session: AsyncSession,
    ) -> None:
        """Test that get_session_stats calculates statistics correctly."""
        service = VoiceService(session)

        # Empty session
        session_start = datetime.now(tz=UTC)
        stats = await service.get_session_stats(
            log_ids=[],
            session_start=session_start,
        )

        assert stats.total_practiced == 0
        assert stats.average_rating == 0.0
        assert stats.time_spent_seconds >= 0

    async def test_get_user_stats_returns_zeros_for_new_user(
        self,
        session: AsyncSession,
        sample_user: UserReadDTO,
    ) -> None:
        """Test that get_user_stats returns zeros for user with no attempts."""
        service = VoiceService(session)

        total, avg = await service.get_user_stats(sample_user.id)

        assert total == 0
        assert avg == 0.0
