"""Tests for config module."""

from typing import Any
from unittest.mock import MagicMock

from src.config import _format_log_record


def create_mock_record(request_id: str | None = None) -> MagicMock:
    """Create a mock loguru record."""
    record: dict[str, Any] = {
        "time": MagicMock(),
        "level": MagicMock(name="INFO"),
        "name": "test_module",
        "function": "test_func",
        "line": 42,
        "message": "Test message",
        "extra": {},
    }

    if request_id:
        record["extra"]["request_id"] = request_id

    mock = MagicMock()
    mock.__getitem__ = lambda _, key: record[key]
    return mock


class TestFormatLogRecord:
    """Tests for _format_log_record function."""

    def test_format_without_request_id(self) -> None:
        """Formats log record without request_id."""
        record = create_mock_record()

        result = _format_log_record(record)

        assert "request_id" not in result
        assert "{name}" in result
        assert "{function}" in result

    def test_format_with_request_id(self) -> None:
        """Formats log record with request_id included."""
        record = create_mock_record(request_id="test-uuid-123")

        result = _format_log_record(record)

        assert "extra[request_id]" in result
        assert "{name}" in result
