"""Tests for gTTS client."""

from unittest.mock import MagicMock, patch

import pytest
from gtts.tts import gTTSError

from src.modules.audio.clients.gtts_client import GTTSClient
from src.modules.vocabulary.enums import Language


@pytest.fixture
def gtts_client() -> GTTSClient:
    """Create gTTS client instance."""
    return GTTSClient()


class TestGTTSClient:
    """Tests for GTTSClient."""

    @pytest.mark.asyncio
    async def test_generate_english(self, gtts_client: GTTSClient) -> None:
        """Test generating audio for English text."""
        with patch("src.modules.audio.clients.gtts_client.gTTS") as mock_gtts:
            mock_instance = MagicMock()
            mock_gtts.return_value = mock_instance
            mock_instance.write_to_fp = MagicMock(side_effect=lambda fp: fp.write(b"fake audio data"))

            result = await gtts_client.generate("hello", Language.EN)

            mock_gtts.assert_called_once_with(text="hello", lang="en")
            assert result == b"fake audio data"

    @pytest.mark.asyncio
    async def test_generate_korean(self, gtts_client: GTTSClient) -> None:
        """Test generating audio for Korean text."""
        with patch("src.modules.audio.clients.gtts_client.gTTS") as mock_gtts:
            mock_instance = MagicMock()
            mock_gtts.return_value = mock_instance
            mock_instance.write_to_fp = MagicMock(side_effect=lambda fp: fp.write(b"korean audio"))

            result = await gtts_client.generate("안녕", Language.KO)

            mock_gtts.assert_called_once_with(text="안녕", lang="ko")
            assert result == b"korean audio"

    @pytest.mark.asyncio
    async def test_generate_russian(self, gtts_client: GTTSClient) -> None:
        """Test generating audio for Russian text."""
        with patch("src.modules.audio.clients.gtts_client.gTTS") as mock_gtts:
            mock_instance = MagicMock()
            mock_gtts.return_value = mock_instance
            mock_instance.write_to_fp = MagicMock(side_effect=lambda fp: fp.write(b"russian audio"))

            result = await gtts_client.generate("привет", Language.RU)

            mock_gtts.assert_called_once_with(text="привет", lang="ru")
            assert result == b"russian audio"

    @pytest.mark.asyncio
    async def test_generate_raises_gtts_error(self, gtts_client: GTTSClient) -> None:
        """Test gTTSError is re-raised after logging."""
        with patch("src.modules.audio.clients.gtts_client.gTTS") as mock_gtts:
            mock_gtts.side_effect = gTTSError("API error")

            with pytest.raises(gTTSError):
                await gtts_client.generate("hello", Language.EN)
