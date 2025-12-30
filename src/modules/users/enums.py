from enum import Enum


class UILanguage(str, Enum):
    RU = "ru"
    EN = "en"
    KO = "ko"


class LanguagePair(str, Enum):
    EN_RU = "en_ru"
    KO_RU = "ko_ru"
