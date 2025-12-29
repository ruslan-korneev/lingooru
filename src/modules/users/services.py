from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError
from src.modules.users.dto import UserCreateDTO, UserReadDTO, UserUpdateDTO
from src.modules.users.repositories import UserRepository


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = UserRepository(session)

    async def get_or_create(self, dto: UserCreateDTO) -> tuple[UserReadDTO, bool]:
        """Get existing user or create new one. Returns (user, created)."""
        existing = await self._repository.get_by_telegram_id(dto.telegram_id)
        if existing:
            return existing, False

        user = await self._repository.save(dto)
        return user, True

    async def get_by_telegram_id(self, telegram_id: int) -> UserReadDTO:
        user = await self._repository.get_by_telegram_id(telegram_id)
        if user is None:
            raise NotFoundError
        return user

    async def get_by_id(self, user_id: UUID) -> UserReadDTO:
        user = await self._repository.get_by_id(user_id)
        if user is None:
            raise NotFoundError
        return user

    async def update(self, user_id: UUID, dto: UserUpdateDTO) -> UserReadDTO:
        """Update user with partial data."""
        user = await self._repository.get_model_by_id(user_id)
        if user is None:
            raise NotFoundError

        update_data = dto.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(user, field, value)

        await self._session.flush()
        await self._session.refresh(user)
        return UserReadDTO.model_validate(user)

    async def create(self, dto: UserCreateDTO) -> UserReadDTO:
        """Create a new user. Raises ConflictError if telegram_id exists."""
        existing = await self._repository.get_by_telegram_id(dto.telegram_id)
        if existing:
            raise ConflictError
        return await self._repository.save(dto)
