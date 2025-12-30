"""Language utilities for Telegram bot handlers."""

from src.modules.users.enums import LanguagePair
from src.modules.vocabulary.enums import Language


def get_language_pair(pair: LanguagePair) -> tuple[Language, Language]:
    """Convert LanguagePair enum to source and target Language tuple.

    Args:
        pair: The user's language pair setting.

    Returns:
        A tuple of (source_language, target_language).
    """
    match pair:
        case LanguagePair.EN_RU:
            return Language.EN, Language.RU
        case LanguagePair.KO_RU:
            return Language.KO, Language.RU
