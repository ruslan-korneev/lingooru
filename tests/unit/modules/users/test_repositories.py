from src.modules.users.dto import UserCreateDTO
from src.modules.users.repositories import UserRepository

TELEGRAM_ID_SAVE = 100100100
TELEGRAM_ID_GET = 200200200
TELEGRAM_ID_NOT_FOUND = 999999999
TELEGRAM_ID_BY_ID = 300300300
TELEGRAM_ID_PAGINATED_BASE = 400400400
PAGINATED_LIMIT = 3
PAGINATED_TOTAL = 5


class TestUserRepository:
    async def test_save_user(
        self,
        user_repository: UserRepository,
    ) -> None:
        dto = UserCreateDTO(
            telegram_id=TELEGRAM_ID_SAVE,
            username="repouser",
            first_name="Repo",
        )

        result = await user_repository.save(dto)

        assert result.id is not None
        assert result.telegram_id == TELEGRAM_ID_SAVE
        assert result.username == "repouser"

    async def test_get_by_telegram_id(
        self,
        user_repository: UserRepository,
    ) -> None:
        dto = UserCreateDTO(telegram_id=TELEGRAM_ID_GET)
        await user_repository.save(dto)

        user = await user_repository.get_by_telegram_id(TELEGRAM_ID_GET)

        assert user is not None
        assert user.telegram_id == TELEGRAM_ID_GET

    async def test_get_by_telegram_id_not_found(
        self,
        user_repository: UserRepository,
    ) -> None:
        user = await user_repository.get_by_telegram_id(999999999)

        assert user is None

    async def test_get_by_id(
        self,
        user_repository: UserRepository,
    ) -> None:
        dto = UserCreateDTO(telegram_id=300300300)
        saved = await user_repository.save(dto)

        user = await user_repository.get_by_id(saved.id)

        assert user is not None
        assert user.id == saved.id

    async def test_get_paginated(
        self,
        user_repository: UserRepository,
    ) -> None:
        # Create multiple users
        for i in range(PAGINATED_TOTAL):
            dto = UserCreateDTO(telegram_id=TELEGRAM_ID_PAGINATED_BASE + i)
            await user_repository.save(dto)

        result = await user_repository.get_paginated(limit=PAGINATED_LIMIT, offset=0)

        assert len(result.items) == PAGINATED_LIMIT
        assert result.total == PAGINATED_TOTAL
