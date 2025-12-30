"""Callback data parsing utilities for Telegram bot handlers."""

from uuid import UUID


def parse_callback_param(data: str | None, index: int, default: str = "") -> str:
    """Safely extract a parameter from callback data at the given index.

    Callback data format: "action:param1:param2:..."

    Args:
        data: The callback data string (e.g., "learn:start:en").
        index: The 0-based index of the parameter to extract.
        default: The default value if index is out of bounds or data is None.

    Returns:
        The parameter at the given index, or the default value.
    """
    if data is None:
        return default
    parts = data.split(":")
    if index < 0 or index >= len(parts):
        return default
    return parts[index]


def parse_callback_uuid(data: str | None, index: int) -> UUID | None:
    """Safely extract a UUID from callback data at the given index.

    Args:
        data: The callback data string (e.g., "audio:play:learn:uuid-here").
        index: The 0-based index of the UUID parameter.

    Returns:
        The parsed UUID, or None if parsing fails or index is out of bounds.
    """
    param = parse_callback_param(data, index)
    if not param:
        return None
    try:
        return UUID(param)
    except ValueError:
        return None


def parse_callback_int(data: str | None, index: int, default: int = 0) -> int:
    """Safely extract an integer from callback data at the given index.

    Args:
        data: The callback data string.
        index: The 0-based index of the integer parameter.
        default: The default value if parsing fails.

    Returns:
        The parsed integer, or the default value.
    """
    param = parse_callback_param(data, index)
    if not param:
        return default
    try:
        return int(param)
    except ValueError:
        return default
