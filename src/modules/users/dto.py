from datetime import datetime
from uuid import UUID

from src.core.types.dto import BaseDTO
from src.modules.users.enums import LanguagePair, UILanguage


class UserCreateDTO(BaseDTO):
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    ui_language: UILanguage = UILanguage.RU
    language_pair: LanguagePair = LanguagePair.EN_RU


class UserReadDTO(BaseDTO):
    id: UUID
    telegram_id: int
    username: str | None
    first_name: str | None
    ui_language: UILanguage
    language_pair: LanguagePair
    timezone: str
    notifications_enabled: bool
    notification_times: list[str]
    created_at: datetime
    updated_at: datetime


class UserUpdateDTO(BaseDTO):
    username: str | None = None
    first_name: str | None = None
    ui_language: UILanguage | None = None
    language_pair: LanguagePair | None = None
    timezone: str | None = None
    notifications_enabled: bool | None = None
    notification_times: list[str] | None = None
