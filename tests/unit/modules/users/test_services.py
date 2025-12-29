import pytest

from src.core.exceptions import ConflictError, NotFoundError
from src.modules.users.dto import UserCreateDTO, UserUpdateDTO
from src.modules.users.models import LanguagePair, UILanguage
from src.modules.users.services import UserService

TELEGRAM_ID_CREATE = 111222333
TELEGRAM_ID_EXISTING = 444555666
TELEGRAM_ID_GET = 777888999
TELEGRAM_ID_NOT_FOUND = 999999999
TELEGRAM_ID_UPDATE_LANG = 111000111
TELEGRAM_ID_UPDATE_PAIR = 222000222
TELEGRAM_ID_CONFLICT = 333000333


class TestUserService:
    async def test_get_or_create_creates_new_user(
        self,
        user_service: UserService,
    ) -> None:
        dto = UserCreateDTO(
            telegram_id=TELEGRAM_ID_CREATE,
            username="newuser",
            first_name="New",
        )

        user, created = await user_service.get_or_create(dto)

        assert created is True
        assert user.telegram_id == TELEGRAM_ID_CREATE
        assert user.username == "newuser"
        assert user.ui_language == UILanguage.RU
        assert user.language_pair == LanguagePair.EN_RU

    async def test_get_or_create_returns_existing(
        self,
        user_service: UserService,
    ) -> None:
        dto = UserCreateDTO(telegram_id=TELEGRAM_ID_EXISTING)

        user1, created1 = await user_service.get_or_create(dto)
        user2, created2 = await user_service.get_or_create(dto)

        assert created1 is True
        assert created2 is False
        assert user1.id == user2.id

    async def test_get_by_telegram_id_success(
        self,
        user_service: UserService,
    ) -> None:
        dto = UserCreateDTO(telegram_id=TELEGRAM_ID_GET)
        await user_service.get_or_create(dto)

        user = await user_service.get_by_telegram_id(TELEGRAM_ID_GET)

        assert user.telegram_id == TELEGRAM_ID_GET

    async def test_get_by_telegram_id_not_found(
        self,
        user_service: UserService,
    ) -> None:
        with pytest.raises(NotFoundError):
            await user_service.get_by_telegram_id(TELEGRAM_ID_NOT_FOUND)

    async def test_update_language(
        self,
        user_service: UserService,
    ) -> None:
        dto = UserCreateDTO(telegram_id=TELEGRAM_ID_UPDATE_LANG)
        user, _ = await user_service.get_or_create(dto)

        updated = await user_service.update(
            user.id,
            UserUpdateDTO(ui_language=UILanguage.EN),
        )

        assert updated.ui_language == UILanguage.EN

    async def test_update_language_pair(
        self,
        user_service: UserService,
    ) -> None:
        dto = UserCreateDTO(telegram_id=TELEGRAM_ID_UPDATE_PAIR)
        user, _ = await user_service.get_or_create(dto)

        updated = await user_service.update(
            user.id,
            UserUpdateDTO(language_pair=LanguagePair.KO_RU),
        )

        assert updated.language_pair == LanguagePair.KO_RU

    async def test_create_raises_conflict_for_duplicate(
        self,
        user_service: UserService,
    ) -> None:
        dto = UserCreateDTO(telegram_id=TELEGRAM_ID_CONFLICT)
        await user_service.create(dto)

        with pytest.raises(ConflictError):
            await user_service.create(dto)
