from typing import Annotated, Any
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, status

from src.core.dependencies.containers import Container
from src.core.types.dto import PaginatedResponse
from src.db.session import AsyncSessionMaker
from src.modules.users.dto import UserCreateDTO, UserReadDTO, UserUpdateDTO
from src.modules.users.repositories import UserRepository
from src.modules.users.services import UserService

router = APIRouter(prefix="/users", tags=["users"])

# Sentinel for dependency injection - typed as Any to avoid type errors with None default
_INJECTED: Any = None


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def create_user(
    dto: UserCreateDTO,
    db_session_maker: Annotated[AsyncSessionMaker, Depends(Provide[Container.db_session_maker])],
) -> UserReadDTO:
    """Create a new user."""
    async with db_session_maker as session:
        service = UserService(session)
        result = await service.create(dto)
        await session.commit()
        return result


@router.get("")
@inject
async def list_users(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db_session_maker: Annotated[
        AsyncSessionMaker,
        Depends(Provide[Container.db_session_maker]),
    ] = _INJECTED,
) -> PaginatedResponse[UserReadDTO]:
    """List all users with pagination."""
    async with db_session_maker as session:
        repository = UserRepository(session)
        paginated = await repository.get_paginated(limit=limit, offset=offset)
        return PaginatedResponse.create(
            items=list(paginated.items),
            total=paginated.total,
            limit=limit,
            offset=offset,
        )


@router.get("/{user_id}")
@inject
async def get_user(
    user_id: UUID,
    db_session_maker: Annotated[AsyncSessionMaker, Depends(Provide[Container.db_session_maker])],
) -> UserReadDTO:
    """Get user by ID."""
    async with db_session_maker as session:
        service = UserService(session)
        return await service.get_by_id(user_id)


@router.get("/telegram/{telegram_id}")
@inject
async def get_user_by_telegram_id(
    telegram_id: int,
    db_session_maker: Annotated[AsyncSessionMaker, Depends(Provide[Container.db_session_maker])],
) -> UserReadDTO:
    """Get user by Telegram ID."""
    async with db_session_maker as session:
        service = UserService(session)
        return await service.get_by_telegram_id(telegram_id)


@router.patch("/{user_id}")
@inject
async def update_user(
    user_id: UUID,
    dto: UserUpdateDTO,
    db_session_maker: Annotated[AsyncSessionMaker, Depends(Provide[Container.db_session_maker])],
) -> UserReadDTO:
    """Update user by ID."""
    async with db_session_maker as session:
        service = UserService(session)
        result = await service.update(user_id, dto)
        await session.commit()
        return result
