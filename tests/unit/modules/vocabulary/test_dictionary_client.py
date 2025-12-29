import pytest
from pytest_httpx import HTTPXMock

from src.modules.vocabulary.dictionary_client import (
    DictionaryResult,
    FreeDictionaryClient,
)

# Sample API response
SAMPLE_API_RESPONSE = [
    {
        "word": "hello",
        "phonetic": "/həˈloʊ/",  # noqa: RUF001
        "phonetics": [
            {"text": "/həˈloʊ/", "audio": "https://example.com/hello.mp3"},  # noqa: RUF001
        ],
        "meanings": [
            {
                "partOfSpeech": "exclamation",
                "definitions": [
                    {
                        "definition": "Used as a greeting.",
                        "example": "Hello, how are you?",
                    }
                ],
            }
        ],
    }
]

SAMPLE_NO_PHONETIC_RESPONSE = [
    {
        "word": "test",
        "phonetics": [
            {"audio": "https://example.com/test.mp3"},
            {"text": "/test/"},
        ],
        "meanings": [
            {
                "partOfSpeech": "noun",
                "definitions": [
                    {
                        "definition": "A procedure.",
                    }
                ],
            }
        ],
    }
]

HTTP_NOT_FOUND = 404
HTTP_SERVER_ERROR = 500


class TestFreeDictionaryClient:
    @pytest.fixture
    async def client(self) -> FreeDictionaryClient:
        return FreeDictionaryClient()

    async def test_lookup_success(
        self,
        client: FreeDictionaryClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url="https://api.dictionaryapi.dev/api/v2/entries/en/hello",
            json=SAMPLE_API_RESPONSE,
        )

        result = await client.lookup("hello")

        assert result is not None
        assert result.word == "hello"
        assert result.phonetic == "/həˈloʊ/"  # noqa: RUF001
        assert result.audio_url == "https://example.com/hello.mp3"
        assert result.definition == "Used as a greeting."
        assert result.example == "Hello, how are you?"

    async def test_lookup_normalizes_input(
        self,
        client: FreeDictionaryClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url="https://api.dictionaryapi.dev/api/v2/entries/en/hello",
            json=SAMPLE_API_RESPONSE,
        )

        result = await client.lookup("  HELLO  ")

        assert result is not None
        assert result.word == "hello"

    async def test_lookup_word_not_found(
        self,
        client: FreeDictionaryClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url="https://api.dictionaryapi.dev/api/v2/entries/en/nonexistent",
            status_code=HTTP_NOT_FOUND,
        )

        result = await client.lookup("nonexistent")

        assert result is None

    async def test_lookup_handles_http_error(
        self,
        client: FreeDictionaryClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url="https://api.dictionaryapi.dev/api/v2/entries/en/error",
            status_code=HTTP_SERVER_ERROR,
        )

        result = await client.lookup("error")

        assert result is None

    async def test_lookup_handles_empty_response(
        self,
        client: FreeDictionaryClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url="https://api.dictionaryapi.dev/api/v2/entries/en/empty",
            json=[],
        )

        result = await client.lookup("empty")

        assert result is None

    async def test_lookup_extracts_phonetic_from_phonetics_list(
        self,
        client: FreeDictionaryClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url="https://api.dictionaryapi.dev/api/v2/entries/en/test",
            json=SAMPLE_NO_PHONETIC_RESPONSE,
        )

        result = await client.lookup("test")

        assert result is not None
        assert result.phonetic == "/test/"
        assert result.audio_url == "https://example.com/test.mp3"

    async def test_lookup_handles_missing_optional_fields(
        self,
        client: FreeDictionaryClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        minimal_response = [
            {
                "word": "minimal",
                "meanings": [{"definitions": [{"definition": "Just a definition."}]}],
            }
        ]

        httpx_mock.add_response(
            url="https://api.dictionaryapi.dev/api/v2/entries/en/minimal",
            json=minimal_response,
        )

        result = await client.lookup("minimal")

        assert result is not None
        assert result.word == "minimal"
        assert result.phonetic is None
        assert result.audio_url is None
        assert result.definition == "Just a definition."
        assert result.example is None


class TestDictionaryResult:
    def test_dataclass_creation(self) -> None:
        result = DictionaryResult(
            word="test",
            phonetic="/test/",
            audio_url="https://example.com/test.mp3",
            definition="A test definition.",
            example="This is a test.",
        )

        assert result.word == "test"
        assert result.phonetic == "/test/"
        assert result.audio_url == "https://example.com/test.mp3"
        assert result.definition == "A test definition."
        assert result.example == "This is a test."

    def test_dataclass_with_none_values(self) -> None:
        result = DictionaryResult(
            word="test",
            phonetic=None,
            audio_url=None,
            definition=None,
            example=None,
        )

        assert result.word == "test"
        assert result.phonetic is None
        assert result.audio_url is None
        assert result.definition is None
        assert result.example is None
