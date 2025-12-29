"""OpenAI client for Whisper transcription and GPT-4o pronunciation evaluation."""

import json
from dataclasses import dataclass

import httpx
from loguru import logger

from src.config import settings

# Threshold for considering pronunciation correct
CORRECT_THRESHOLD = 4


@dataclass
class TranscriptionResult:
    """Result from Whisper transcription."""

    text: str
    duration_seconds: float | None = None


@dataclass
class PronunciationEvaluation:
    """Result from GPT-4o pronunciation check."""

    rating: int  # 1-5
    feedback: str
    is_correct: bool


class OpenAIClient:
    """Client for OpenAI Whisper and GPT-4o APIs."""

    WHISPER_URL = "https://api.openai.com/v1/audio/transcriptions"
    CHAT_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(self) -> None:
        api_key = settings.openai.api_key.get_secret_value()
        self._client = httpx.AsyncClient(
            timeout=settings.openai.timeout_seconds,
            headers={
                "Authorization": f"Bearer {api_key}",
            },
        )

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "en",
    ) -> TranscriptionResult:
        """Transcribe audio using Whisper API.

        Args:
            audio_bytes: Audio data in OGG format (from Telegram voice messages)
            language: ISO 639-1 language code (en, ko, ru)

        Returns:
            TranscriptionResult with text and optional duration
        """
        try:
            files = {"file": ("audio.ogg", audio_bytes, "audio/ogg")}
            data = {
                "model": settings.openai.whisper_model,
                "language": language,
                "response_format": "verbose_json",
            }

            response = await self._client.post(
                self.WHISPER_URL,
                files=files,
                data=data,
            )
            response.raise_for_status()
            result = response.json()

            return TranscriptionResult(
                text=result.get("text", "").strip(),
                duration_seconds=result.get("duration"),
            )

        except httpx.HTTPError as e:
            logger.error(f"Whisper API error: {e}")
            raise

    async def check_pronunciation(
        self,
        expected: str,
        transcribed: str,
        language: str,
        phonetic: str | None = None,
    ) -> PronunciationEvaluation:
        """Check pronunciation using GPT-4o.

        Args:
            expected: The word/phrase user should have pronounced
            transcribed: What Whisper transcribed from user's audio
            language: Language code (en, ko)
            phonetic: Optional IPA phonetic transcription

        Returns:
            PronunciationEvaluation with rating, feedback, and is_correct flag
        """
        language_name = {
            "en": "English",
            "ko": "Korean",
        }.get(language, "English")

        phonetic_hint = f"\nPhonetic transcription: {phonetic}" if phonetic else ""

        prompt = f"""You are a {language_name} pronunciation teacher.
The user tried to pronounce: "{expected}"{phonetic_hint}
Whisper transcribed their audio as: "{transcribed}"

Rate the pronunciation from 1 to 5:
1 = Very poor, completely different
2 = Poor, major errors
3 = Fair, noticeable errors but understandable
4 = Good, minor errors
5 = Excellent, native-like pronunciation

Respond in JSON format:
{{
    "rating": <1-5>,
    "feedback": "<brief feedback in Russian, max 2 sentences>",
    "is_correct": <true if rating >= 4>
}}

Give feedback in Russian language. Be encouraging but honest."""

        try:
            response = await self._client.post(
                self.CHAT_URL,
                json={
                    "model": settings.openai.gpt_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.3,
                },
            )
            response.raise_for_status()
            result = response.json()

            content = result["choices"][0]["message"]["content"]
            data = json.loads(content)

            rating = max(1, min(5, int(data.get("rating", 3))))

            return PronunciationEvaluation(
                rating=rating,
                feedback=data.get("feedback", ""),
                is_correct=data.get("is_correct", rating >= CORRECT_THRESHOLD),
            )

        except httpx.HTTPError as e:
            logger.error(f"GPT-4o API error: {e}")
            raise
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse GPT-4o response: {e}")
            # Return a default response if parsing fails
            return PronunciationEvaluation(
                rating=3,
                feedback="Не удалось оценить произношение. Попробуй ещё раз.",  # noqa: RUF001
                is_correct=False,
            )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()


class _OpenAIClientHolder:
    """Holder for singleton OpenAI client instance."""

    _instance: OpenAIClient | None = None

    @classmethod
    def get(cls) -> OpenAIClient:
        if cls._instance is None:
            cls._instance = OpenAIClient()
        return cls._instance


def get_openai_client() -> OpenAIClient:
    """Get the singleton OpenAI client instance."""
    return _OpenAIClientHolder.get()
