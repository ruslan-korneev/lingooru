"""Tests for gTTS client."""

from unittest.mock import MagicMock, patch

import pytest

from src.modules.audio.clients.gtts_client import GTTSClient


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
            mock_instance.write_to_fp = MagicMock(
                side_effect=lambda fp: fp.write(b"fake audio data")
            )

            result = await gtts_client.generate("hello", "en")

            mock_gtts.assert_called_once_with(text="hello", lang="en")
            assert result == b"fake audio data"

    @pytest.mark.asyncio
    async def test_generate_korean(self, gtts_client: GTTSClient) -> None:
        """Test generating audio for Korean text."""
        with patch("src.modules.audio.clients.gtts_client.gTTS") as mock_gtts:
            mock_instance = MagicMock()
            mock_gtts.return_value = mock_instance
            mock_instance.write_to_fp = MagicMock(
                side_effect=lambda fp: fp.write(b"korean audio")
            )

            result = await gtts_client.generate("안녕", "ko")

            mock_gtts.assert_called_once_with(text="안녕", lang="ko")
            assert result == b"korean audio"

    @pytest.mark.asyncio
    async def test_generate_unsupported_language_defaults_to_english(
        self, gtts_client: GTTSClient
    ) -> None:
        """Test that unsupported language falls back to English."""
        with patch("src.modules.audio.clients.gtts_client.gTTS") as mock_gtts:
            mock_instance = MagicMock()
            mock_gtts.return_value = mock_instance
            mock_instance.write_to_fp = MagicMock(
                side_effect=lambda fp: fp.write(b"audio")
            )

            await gtts_client.generate("test", "unknown")

            # Should fallback to 'en'
            mock_gtts.assert_called_once_with(text="test", lang="en")

    def test_language_map(self, gtts_client: GTTSClient) -> None:
        """Test language mapping."""
        assert gtts_client.LANGUAGE_MAP["en"] == "en"
        assert gtts_client.LANGUAGE_MAP["ko"] == "ko"
        assert gtts_client.LANGUAGE_MAP["ru"] == "ru"
