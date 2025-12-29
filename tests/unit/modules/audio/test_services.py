"""Tests for AudioService."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.audio.services import AudioService
from src.modules.vocabulary.models import Language, Word


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def audio_service(mock_session: AsyncMock) -> AudioService:
    """Create AudioService instance with mocked dependencies."""
    return AudioService(mock_session)


@pytest.fixture
def sample_word() -> Word:
    """Create sample word for testing."""
    word = Word()
    word.id = uuid.uuid4()
    word.text = "apple"
    word.language = Language.EN
    word.phonetic = "/ˈæpl/"  # noqa: RUF001
    word.audio_url = None
    word.audio_source = None
    return word


@pytest.fixture
def sample_word_with_audio() -> Word:
    """Create sample word with existing audio."""
    word = Word()
    word.id = uuid.uuid4()
    word.text = "hello"
    word.language = Language.EN
    word.phonetic = "/həˈloʊ/"  # noqa: RUF001
    word.audio_url = "https://example.com/hello.mp3"
    word.audio_source = "dictionary_api"
    return word


class TestAudioService:
    """Tests for AudioService."""

    @pytest.mark.asyncio
    async def test_get_audio_url_returns_existing_url(
        self,
        audio_service: AudioService,
        mock_session: AsyncMock,
        sample_word_with_audio: Word,
    ) -> None:
        """Test that existing audio_url is returned without generation."""
        # Mock get_word
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_word_with_audio
        mock_session.execute.return_value = mock_result

        result = await audio_service.get_audio_url(sample_word_with_audio.id)

        assert result == "https://example.com/hello.mp3"

    @pytest.mark.asyncio
    async def test_get_audio_url_generates_for_missing(
        self,
        audio_service: AudioService,
        mock_session: AsyncMock,
        sample_word: Word,
    ) -> None:
        """Test that audio is generated when url is missing."""
        # Mock get_word
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_word
        mock_session.execute.return_value = mock_result

        # Mock gTTS and S3
        with (
            patch.object(audio_service, "_gtts") as mock_gtts,
            patch.object(audio_service, "_s3") as mock_s3,
        ):
            mock_gtts.generate = AsyncMock(return_value=b"audio data")
            mock_s3.upload_audio = AsyncMock(
                return_value="https://s3.example.com/words/123.mp3"
            )

            result = await audio_service.get_audio_url(sample_word.id)

            assert result == "https://s3.example.com/words/123.mp3"
            mock_gtts.generate.assert_called_once_with(
                text="apple",
                language="en",
            )

    @pytest.mark.asyncio
    async def test_get_audio_url_returns_none_for_nonexistent_word(
        self,
        audio_service: AudioService,
        mock_session: AsyncMock,
    ) -> None:
        """Test that None is returned for non-existent word."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await audio_service.get_audio_url(uuid.uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_audio_bytes_downloads_from_url(
        self,
        audio_service: AudioService,
        mock_session: AsyncMock,
        sample_word_with_audio: Word,
    ) -> None:
        """Test downloading audio bytes from URL."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_word_with_audio
        mock_session.execute.return_value = mock_result

        with patch("src.modules.audio.services.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"audio content"

            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await audio_service.get_audio_bytes(sample_word_with_audio.id)

            assert result == b"audio content"

    @pytest.mark.asyncio
    async def test_get_audio_bytes_returns_none_for_missing_word(
        self,
        audio_service: AudioService,
        mock_session: AsyncMock,
    ) -> None:
        """Test that None is returned when word doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await audio_service.get_audio_bytes(uuid.uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_generate_and_cache_unsupported_language(
        self,
        audio_service: AudioService,
    ) -> None:
        """Test that unsupported language returns None."""
        word = Word()
        word.id = uuid.uuid4()
        word.text = "test"
        word.language = Language.RU  # Russian not supported for TTS in our setup

        result = await audio_service._generate_and_cache(word)  # noqa: SLF001

        assert result is None
