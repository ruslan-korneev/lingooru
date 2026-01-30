"""Unit tests for greeting utilities."""

from src.bot.constants import GREETINGS, Greeting
from src.bot.utils.greeting import format_greeting, get_random_greeting


class TestGreetingNamedTuple:
    """Test cases for Greeting NamedTuple structure."""

    def test_greeting_has_required_fields(self) -> None:
        """Greeting has language_code, flag, native_text, transcription fields."""
        greeting = Greeting(
            language_code="en",
            flag="🇬🇧",
            native_text="Hello!",
            transcription="Hello!",
        )
        assert greeting.language_code == "en"
        assert greeting.flag == "🇬🇧"
        assert greeting.native_text == "Hello!"
        assert greeting.transcription == "Hello!"

    def test_greeting_is_immutable(self) -> None:
        """Greeting is immutable (NamedTuple behavior)."""
        greeting = Greeting("en", "🇬🇧", "Hello!", "Hello!")
        assert isinstance(greeting, tuple)


class TestGreetingsConstant:
    """Test cases for GREETINGS constant."""

    def test_greetings_is_not_empty(self) -> None:
        """GREETINGS contains at least 10 languages."""
        assert len(GREETINGS) >= 10  # noqa: PLR2004

    def test_greetings_has_valid_structure(self) -> None:
        """All greetings have non-empty fields."""
        for greeting in GREETINGS:
            assert isinstance(greeting, Greeting)
            assert greeting.language_code, "language_code is empty"
            assert greeting.flag, "flag is empty"
            assert greeting.native_text, "native_text is empty"
            assert greeting.transcription, "transcription is empty"

    def test_greetings_contains_english(self) -> None:
        """GREETINGS contains English."""
        lang_codes = [g.language_code for g in GREETINGS]
        assert "en" in lang_codes

    def test_greetings_contains_korean(self) -> None:
        """GREETINGS contains Korean."""
        lang_codes = [g.language_code for g in GREETINGS]
        assert "ko" in lang_codes


class TestGetRandomGreeting:
    """Test cases for get_random_greeting function."""

    def test_returns_greeting_type(self) -> None:
        """get_random_greeting returns a Greeting."""
        result = get_random_greeting()
        assert isinstance(result, Greeting)

    def test_returns_greeting_from_greetings(self) -> None:
        """get_random_greeting returns a greeting from GREETINGS."""
        result = get_random_greeting()
        assert result in GREETINGS

    def test_is_random_over_multiple_calls(self) -> None:
        """get_random_greeting returns different results over 100 calls."""
        results = {get_random_greeting() for _ in range(100)}
        # With 15 greetings and 100 calls, we should get at least 5 different ones
        assert len(results) >= 5  # noqa: PLR2004


class TestFormatGreeting:
    """Test cases for format_greeting function."""

    def test_format_korean_greeting(self) -> None:
        """format_greeting correctly formats Korean greeting."""
        greeting = Greeting("ko", "🇰🇷", "안녕하세요!", "Annyeonghaseyo!")
        result = format_greeting(greeting)
        assert result == "🇰🇷 안녕하세요!\n(Annyeonghaseyo!)"

    def test_format_english_greeting(self) -> None:
        """format_greeting correctly formats English greeting."""
        greeting = Greeting("en", "🇬🇧", "Hello!", "Hello!")
        result = format_greeting(greeting)
        assert result == "🇬🇧 Hello!\n(Hello!)"

    def test_format_contains_flag(self) -> None:
        """format_greeting output starts with flag."""
        greeting = Greeting("ja", "🇯🇵", "こんにちは!", "Konnichiwa!")
        result = format_greeting(greeting)
        assert result.startswith("🇯🇵")

    def test_format_contains_transcription_in_parentheses(self) -> None:
        """format_greeting output contains transcription in parentheses."""
        greeting = Greeting("fr", "🇫🇷", "Bonjour!", "Bon-zhoor!")
        result = format_greeting(greeting)
        assert "(Bon-zhoor!)" in result

    def test_format_has_newline_between_text_and_transcription(self) -> None:
        """format_greeting has newline between native text and transcription."""
        greeting = Greeting("de", "🇩🇪", "Hallo!", "Hallo!")
        result = format_greeting(greeting)
        assert "\n" in result
        lines = result.split("\n")
        assert len(lines) == 2  # noqa: PLR2004
