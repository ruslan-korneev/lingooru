from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.types.repositories import BaseRepository
from src.modules.users.dto import UserCreateDTO, UserReadDTO
from src.modules.users.models import User


class UserRepository(BaseRepository[User, UserCreateDTO, UserReadDTO]):
    _model = User
    _create_dto = UserCreateDTO
    _read_dto = UserReadDTO

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_telegram_id(self, telegram_id: int) -> UserReadDTO | None:
        query = select(self._model).where(self._model.telegram_id == telegram_id)
        result = await self._session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return None
        return self._read_dto.model_validate(instance)

    async def get_by_id(self, user_id: UUID) -> UserReadDTO | None:
        query = select(self._model).where(self._model.id == user_id)
        result = await self._session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return None
        return self._read_dto.model_validate(instance)

    async def get_model_by_id(self, user_id: UUID) -> User | None:
        query = select(self._model).where(self._model.id == user_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
