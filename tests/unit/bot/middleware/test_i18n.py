"""Tests for i18n middleware (UserLocaleManager)."""

from unittest.mock import MagicMock

from aiogram.types import TelegramObject, User

from src.bot.middleware.i18n import UserLocaleManager
from src.modules.users.dto import UserReadDTO
from src.modules.users.models import LanguagePair, UILanguage


def create_user_dto(ui_language: UILanguage) -> UserReadDTO:
    """Create a mock UserReadDTO."""
    from datetime import UTC, datetime
    from uuid import uuid4

    return UserReadDTO(
        id=uuid4(),
        telegram_id=123,
        username="test",
        first_name="Test",
        ui_language=ui_language,
        language_pair=LanguagePair.EN_RU,
        timezone="UTC",
        notifications_enabled=True,
        notification_times=["09:00"],
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )


class TestUserLocaleManager:
    """Tests for UserLocaleManager class."""

    async def test_returns_db_user_locale_when_present(self) -> None:
        """Returns UI language from db_user when available."""
        manager = UserLocaleManager()
        event = MagicMock(spec=TelegramObject)
        db_user = create_user_dto(UILanguage.EN)

        locale = await manager.get_locale(event, db_user=db_user)

        assert locale == "en"

    async def test_returns_db_user_locale_ru(self) -> None:
        """Returns Russian when db_user has RU locale."""
        manager = UserLocaleManager()
        event = MagicMock(spec=TelegramObject)
        db_user = create_user_dto(UILanguage.RU)

        locale = await manager.get_locale(event, db_user=db_user)

        assert locale == "ru"

    async def test_returns_db_user_locale_ko(self) -> None:
        """Returns Korean when db_user has KO locale."""
        manager = UserLocaleManager()
        event = MagicMock(spec=TelegramObject)
        db_user = create_user_dto(UILanguage.KO)

        locale = await manager.get_locale(event, db_user=db_user)

        assert locale == "ko"

    async def test_fallback_to_telegram_language_ru(self) -> None:
        """Falls back to Telegram user language when no db_user."""
        manager = UserLocaleManager()
        event = MagicMock(spec=TelegramObject)
        tg_user = User(id=123, is_bot=False, first_name="Test", language_code="ru")

        locale = await manager.get_locale(event, event_from_user=tg_user, db_user=None)

        assert locale == "ru"

    async def test_fallback_to_telegram_language_en(self) -> None:
        """Falls back to Telegram English language."""
        manager = UserLocaleManager()
        event = MagicMock(spec=TelegramObject)
        tg_user = User(id=123, is_bot=False, first_name="Test", language_code="en")

        locale = await manager.get_locale(event, event_from_user=tg_user, db_user=None)

        assert locale == "en"

    async def test_fallback_to_telegram_language_ko(self) -> None:
        """Falls back to Telegram Korean language."""
        manager = UserLocaleManager()
        event = MagicMock(spec=TelegramObject)
        tg_user = User(id=123, is_bot=False, first_name="Test", language_code="ko")

        locale = await manager.get_locale(event, event_from_user=tg_user, db_user=None)

        assert locale == "ko"

    async def test_unsupported_telegram_language_defaults_to_ru(self) -> None:
        """Defaults to Russian for unsupported Telegram language."""
        manager = UserLocaleManager()
        event = MagicMock(spec=TelegramObject)
        tg_user = User(id=123, is_bot=False, first_name="Test", language_code="de")

        locale = await manager.get_locale(event, event_from_user=tg_user, db_user=None)

        assert locale == "ru"

    async def test_no_telegram_user_defaults_to_ru(self) -> None:
        """Defaults to Russian when no Telegram user."""
        manager = UserLocaleManager()
        event = MagicMock(spec=TelegramObject)

        locale = await manager.get_locale(event, event_from_user=None, db_user=None)

        assert locale == "ru"

    async def test_telegram_user_no_language_code_defaults_to_ru(self) -> None:
        """Defaults to Russian when Telegram user has no language_code."""
        manager = UserLocaleManager()
        event = MagicMock(spec=TelegramObject)
        tg_user = User(id=123, is_bot=False, first_name="Test", language_code=None)

        locale = await manager.get_locale(event, event_from_user=tg_user, db_user=None)

        assert locale == "ru"

    async def test_db_user_takes_precedence_over_telegram_user(self) -> None:
        """db_user locale takes precedence over Telegram user language."""
        manager = UserLocaleManager()
        event = MagicMock(spec=TelegramObject)
        db_user = create_user_dto(UILanguage.KO)
        tg_user = User(id=123, is_bot=False, first_name="Test", language_code="en")

        locale = await manager.get_locale(event, event_from_user=tg_user, db_user=db_user)

        assert locale == "ko"

    async def test_set_locale_is_noop(self) -> None:
        """set_locale does nothing (locale saved in handler)."""
        manager = UserLocaleManager()
        event = MagicMock(spec=TelegramObject)

        # Should not raise any exception
        await manager.set_locale("en", event=event)
