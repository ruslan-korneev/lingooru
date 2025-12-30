from enum import Enum


class Language(str, Enum):
    """Supported languages."""

    EN = "en"
    KO = "ko"
    RU = "ru"
