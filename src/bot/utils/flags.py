from src.modules.vocabulary.enums import Language

LANGUAGE_FLAGS: dict[Language, str] = {
    Language.EN: "🇬🇧",
    Language.KO: "🇰🇷",
    Language.RU: "🇷🇺",
}


def get_flag(language: Language) -> str:
    """Get flag emoji for a language."""
    return LANGUAGE_FLAGS.get(language, "🌐")
