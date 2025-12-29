from dataclasses import dataclass
from http import HTTPStatus
from typing import Any

import httpx
from loguru import logger


@dataclass
class DictionaryResult:
    """Result from dictionary API lookup."""

    word: str
    phonetic: str | None
    audio_url: str | None
    definition: str | None
    example: str | None


class FreeDictionaryClient:
    """Client for Free Dictionary API (dictionaryapi.dev)."""

    BASE_URL = "https://api.dictionaryapi.dev/api/v2/entries/en"

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=10.0)

    async def lookup(self, word: str) -> DictionaryResult | None:
        """Look up an English word in the dictionary."""
        try:
            response = await self._client.get(f"{self.BASE_URL}/{word.lower().strip()}")

            if response.status_code == HTTPStatus.NOT_FOUND:
                logger.debug(f"Word '{word}' not found in dictionary")
                return None

            response.raise_for_status()
            data = response.json()

            if not data:
                return None

            return self._parse_response(data, word)

        except httpx.HTTPError as e:
            logger.error(f"Dictionary API error for '{word}': {e}")
            return None

    def _parse_response(
        self,
        data: list[dict[str, Any]],
        fallback_word: str,
    ) -> DictionaryResult:
        """Parse API response into DictionaryResult."""
        entry = data[0]

        # Extract phonetic
        phonetic = entry.get("phonetic")
        if not phonetic and entry.get("phonetics"):
            for p in entry["phonetics"]:
                if p.get("text"):
                    phonetic = p["text"]
                    break

        # Extract audio URL
        audio_url = None
        for p in entry.get("phonetics", []):
            if p.get("audio"):
                audio_url = p["audio"]
                break

        # Extract definition and example
        definition = None
        example = None
        for meaning in entry.get("meanings", []):
            for defn in meaning.get("definitions", []):
                if defn.get("definition"):
                    definition = defn["definition"]
                    example = defn.get("example")
                    break
            if definition:
                break

        return DictionaryResult(
            word=entry.get("word", fallback_word),
            phonetic=phonetic,
            audio_url=audio_url,
            definition=definition,
            example=example,
        )

    async def close(self) -> None:
        await self._client.aclose()


class _DictionaryClientHolder:
    """Holder for singleton dictionary client instance."""

    _instance: FreeDictionaryClient | None = None

    @classmethod
    def get(cls) -> FreeDictionaryClient:
        if cls._instance is None:
            cls._instance = FreeDictionaryClient()
        return cls._instance


def get_dictionary_client() -> FreeDictionaryClient:
    return _DictionaryClientHolder.get()
