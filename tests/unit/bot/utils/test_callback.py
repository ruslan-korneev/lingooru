"""Unit tests for callback data parsing utilities."""

from uuid import UUID

from src.bot.utils.callback import (
    parse_callback_int,
    parse_callback_param,
    parse_callback_uuid,
)


class TestParseCallbackParam:
    """Test cases for parse_callback_param function."""

    def test_returns_param_at_index(self) -> None:
        """Should return parameter at given index."""
        result = parse_callback_param("learn:start:en", 1)
        assert result == "start"

    def test_returns_first_param(self) -> None:
        """Should return first parameter (index 0)."""
        result = parse_callback_param("menu:main", 0)
        assert result == "menu"

    def test_returns_last_param(self) -> None:
        """Should return last parameter."""
        result = parse_callback_param("review:rate:5", 2)
        assert result == "5"

    def test_returns_default_for_none_data(self) -> None:
        """Should return default when data is None."""
        result = parse_callback_param(None, 0)
        assert result == ""

    def test_returns_custom_default_for_none_data(self) -> None:
        """Should return custom default when data is None."""
        result = parse_callback_param(None, 0, default="fallback")
        assert result == "fallback"

    def test_returns_default_for_index_out_of_bounds(self) -> None:
        """Should return default when index exceeds parts count."""
        result = parse_callback_param("learn:start", 5)
        assert result == ""

    def test_returns_default_for_negative_index(self) -> None:
        """Should return default for negative index."""
        result = parse_callback_param("learn:start", -1)
        assert result == ""

    def test_handles_empty_string(self) -> None:
        """Should handle empty string data."""
        result = parse_callback_param("", 0)
        assert result == ""

    def test_handles_single_part(self) -> None:
        """Should handle single part without colons."""
        result = parse_callback_param("menu", 0)
        assert result == "menu"

    def test_handles_empty_parts(self) -> None:
        """Should handle empty parts between colons."""
        result = parse_callback_param("learn::en", 1)
        assert result == ""


class TestParseCallbackUuid:
    """Test cases for parse_callback_uuid function."""

    def test_returns_valid_uuid(self) -> None:
        """Should parse and return valid UUID."""
        uuid_str = "12345678-1234-5678-1234-567812345678"
        result = parse_callback_uuid(f"audio:play:learn:{uuid_str}", 3)
        assert result == UUID(uuid_str)

    def test_returns_none_for_invalid_uuid(self) -> None:
        """Should return None for invalid UUID string."""
        result = parse_callback_uuid("audio:play:learn:not-a-uuid", 3)
        assert result is None

    def test_returns_none_for_none_data(self) -> None:
        """Should return None when data is None."""
        result = parse_callback_uuid(None, 0)
        assert result is None

    def test_returns_none_for_index_out_of_bounds(self) -> None:
        """Should return None when index exceeds parts count."""
        result = parse_callback_uuid("audio:play", 5)
        assert result is None

    def test_returns_none_for_empty_param(self) -> None:
        """Should return None for empty parameter."""
        result = parse_callback_uuid("audio:play::", 3)
        assert result is None


class TestParseCallbackInt:
    """Test cases for parse_callback_int function."""

    def test_returns_valid_int(self) -> None:
        """Should parse and return valid integer."""
        result = parse_callback_int("review:rate:5", 2)
        assert result == 5  # noqa: PLR2004

    def test_returns_negative_int(self) -> None:
        """Should parse negative integer."""
        result = parse_callback_int("data:-10", 1)
        assert result == -10  # noqa: PLR2004

    def test_returns_default_for_invalid_int(self) -> None:
        """Should return default for non-integer string."""
        result = parse_callback_int("review:rate:abc", 2)
        assert result == 0

    def test_returns_custom_default_for_invalid_int(self) -> None:
        """Should return custom default for invalid integer."""
        result = parse_callback_int("review:rate:abc", 2, default=1)
        assert result == 1

    def test_returns_default_for_none_data(self) -> None:
        """Should return default when data is None."""
        result = parse_callback_int(None, 0)
        assert result == 0

    def test_returns_default_for_index_out_of_bounds(self) -> None:
        """Should return default when index exceeds parts count."""
        result = parse_callback_int("review:rate", 5)
        assert result == 0

    def test_returns_default_for_empty_param(self) -> None:
        """Should return default for empty parameter."""
        result = parse_callback_int("review:rate:", 2)
        assert result == 0

    def test_parses_zero(self) -> None:
        """Should correctly parse zero."""
        result = parse_callback_int("data:0", 1)
        assert result == 0


class TestCallbackIndexConstants:
    """Test cases for callback index constants."""

    def test_callback_action_index_is_zero(self) -> None:
        """Action is always first part (index 0)."""
        from src.bot.utils.callback import CALLBACK_ACTION_INDEX

        assert CALLBACK_ACTION_INDEX == 0

    def test_callback_subaction_index_is_one(self) -> None:
        """Subaction is always second part (index 1)."""
        from src.bot.utils.callback import CALLBACK_SUBACTION_INDEX

        assert CALLBACK_SUBACTION_INDEX == 1

    def test_callback_value_index_is_two(self) -> None:
        """Value is always third part (index 2)."""
        from src.bot.utils.callback import CALLBACK_VALUE_INDEX

        assert CALLBACK_VALUE_INDEX == 2  # noqa: PLR2004

    def test_constants_work_with_parse_callback_param(self) -> None:
        """Constants should work correctly with parse_callback_param."""
        from src.bot.utils.callback import (
            CALLBACK_ACTION_INDEX,
            CALLBACK_SUBACTION_INDEX,
            CALLBACK_VALUE_INDEX,
        )

        data = "settings:lang:en"

        assert parse_callback_param(data, CALLBACK_ACTION_INDEX) == "settings"
        assert parse_callback_param(data, CALLBACK_SUBACTION_INDEX) == "lang"
        assert parse_callback_param(data, CALLBACK_VALUE_INDEX) == "en"


class TestExtractCallbackMessage:
    """Test cases for extract_callback_message function."""

    def test_returns_message_when_valid(self) -> None:
        """Should return Message when callback has valid data and message."""
        from unittest.mock import MagicMock

        from aiogram.types import Message

        from src.bot.utils.callback import extract_callback_message

        mock_message = MagicMock(spec=Message)
        mock_callback = MagicMock()
        mock_callback.data = "settings:lang:en"
        mock_callback.message = mock_message

        result = extract_callback_message(mock_callback)

        assert result is mock_message

    def test_returns_none_when_no_data(self) -> None:
        """Should return None when callback.data is None."""
        from unittest.mock import MagicMock

        from src.bot.utils.callback import extract_callback_message

        mock_callback = MagicMock()
        mock_callback.data = None
        mock_callback.message = MagicMock()

        result = extract_callback_message(mock_callback)

        assert result is None

    def test_returns_none_when_no_message(self) -> None:
        """Should return None when callback.message is None."""
        from unittest.mock import MagicMock

        from src.bot.utils.callback import extract_callback_message

        mock_callback = MagicMock()
        mock_callback.data = "settings:lang:en"
        mock_callback.message = None

        result = extract_callback_message(mock_callback)

        assert result is None

    def test_returns_none_when_message_is_inaccessible(self) -> None:
        """Should return None when message is InaccessibleMessage."""
        from unittest.mock import MagicMock

        from aiogram.types import InaccessibleMessage

        from src.bot.utils.callback import extract_callback_message

        mock_inaccessible = MagicMock(spec=InaccessibleMessage)
        mock_callback = MagicMock()
        mock_callback.data = "settings:lang:en"
        mock_callback.message = mock_inaccessible

        result = extract_callback_message(mock_callback)

        assert result is None

    def test_returns_none_when_data_is_empty_string(self) -> None:
        """Should return None when callback.data is empty string (falsy)."""
        from unittest.mock import MagicMock

        from aiogram.types import Message

        from src.bot.utils.callback import extract_callback_message

        mock_message = MagicMock(spec=Message)
        mock_callback = MagicMock()
        mock_callback.data = ""
        mock_callback.message = mock_message

        result = extract_callback_message(mock_callback)

        assert result is None
