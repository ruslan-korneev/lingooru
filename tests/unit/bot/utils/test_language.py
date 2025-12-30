"""Unit tests for language utilities."""

from src.bot.utils.language import get_language_pair
from src.modules.users.models import LanguagePair
from src.modules.vocabulary.models import Language


class TestGetLanguagePair:
    """Test cases for get_language_pair function."""

    def test_en_ru_pair(self) -> None:
        """Should return EN and RU for EN_RU pair."""
        source, target = get_language_pair(LanguagePair.EN_RU)
        assert source == Language.EN
        assert target == Language.RU

    def test_ko_ru_pair(self) -> None:
        """Should return KO and RU for KO_RU pair."""
        source, target = get_language_pair(LanguagePair.KO_RU)
        assert source == Language.KO
        assert target == Language.RU

    def test_returns_tuple(self) -> None:
        """Should return a tuple of two Language values."""
        result = get_language_pair(LanguagePair.EN_RU)
        assert isinstance(result, tuple)
        assert len(result) == 2  # noqa: PLR2004
        assert all(isinstance(lang, Language) for lang in result)
