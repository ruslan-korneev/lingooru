"""Unit tests for OpenAI client."""

import json

import pytest
from pytest_httpx import HTTPXMock

from src.modules.voice.openai_client import OpenAIClient


class TestOpenAIClient:
    """Test cases for OpenAI client."""

    @pytest.fixture
    def openai_client(self) -> OpenAIClient:
        """Create an OpenAI client instance."""
        return OpenAIClient()

    async def test_transcribe_parses_response(
        self,
        openai_client: OpenAIClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Test that transcribe parses Whisper response correctly."""
        httpx_mock.add_response(
            url="https://api.openai.com/v1/audio/transcriptions",
            json={
                "text": "hello world",
                "duration": 2.5,
            },
        )

        result = await openai_client.transcribe(
            audio_bytes=b"fake_audio",
            language="en",
        )

        assert result.text == "hello world"
        assert result.duration_seconds == 2.5  # noqa: PLR2004

    async def test_transcribe_handles_missing_duration(
        self,
        openai_client: OpenAIClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Test that transcribe handles missing duration."""
        httpx_mock.add_response(
            url="https://api.openai.com/v1/audio/transcriptions",
            json={
                "text": "test",
            },
        )

        result = await openai_client.transcribe(
            audio_bytes=b"fake_audio",
            language="en",
        )

        assert result.text == "test"
        assert result.duration_seconds is None

    async def test_check_pronunciation_parses_response(
        self,
        openai_client: OpenAIClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Test that check_pronunciation parses GPT-4o response correctly."""
        response_content = json.dumps(
            {
                "rating": 4,
                "feedback": "Good job!",
                "is_correct": True,
            }
        )

        httpx_mock.add_response(
            url="https://api.openai.com/v1/chat/completions",
            json={
                "choices": [
                    {
                        "message": {
                            "content": response_content,
                        }
                    }
                ]
            },
        )

        result = await openai_client.check_pronunciation(
            expected="hello",
            transcribed="hello",
            language="en",
        )

        assert result.rating == 4  # noqa: PLR2004
        assert result.feedback == "Good job!"
        assert result.is_correct is True

    async def test_check_pronunciation_clamps_rating(
        self,
        openai_client: OpenAIClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Test that rating is clamped to 1-5 range."""
        # Test rating > 5
        httpx_mock.add_response(
            url="https://api.openai.com/v1/chat/completions",
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "rating": 10,
                                    "feedback": "Perfect!",
                                    "is_correct": True,
                                }
                            ),
                        }
                    }
                ]
            },
        )

        result = await openai_client.check_pronunciation(
            expected="test",
            transcribed="test",
            language="en",
        )

        assert result.rating == 5  # noqa: PLR2004

    async def test_check_pronunciation_handles_malformed_json(
        self,
        openai_client: OpenAIClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Test that check_pronunciation handles malformed JSON gracefully."""
        httpx_mock.add_response(
            url="https://api.openai.com/v1/chat/completions",
            json={
                "choices": [
                    {
                        "message": {
                            "content": "not valid json",
                        }
                    }
                ]
            },
        )

        result = await openai_client.check_pronunciation(
            expected="test",
            transcribed="test",
            language="en",
        )

        # Should return default values
        assert result.rating == 3  # noqa: PLR2004
        assert result.is_correct is False

    async def test_check_pronunciation_includes_phonetic_in_prompt(
        self,
        openai_client: OpenAIClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Test that phonetic transcription is included in prompt."""
        httpx_mock.add_response(
            url="https://api.openai.com/v1/chat/completions",
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "rating": 5,
                                    "feedback": "Excellent!",
                                    "is_correct": True,
                                }
                            ),
                        }
                    }
                ]
            },
        )

        await openai_client.check_pronunciation(
            expected="hello",
            transcribed="hello",
            language="en",
            phonetic="/həˈloʊ/",  # noqa: RUF001
        )

        # Verify request was made
        request = httpx_mock.get_request()
        assert request is not None

        # Check that phonetic was included in the request body
        request_body = json.loads(request.content)
        prompt = request_body["messages"][0]["content"]
        assert "/həˈloʊ/" in prompt  # noqa: RUF001
