"""Tests for BaseRepository and related types."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.users.dto import UserCreateDTO
from src.modules.users.models import User
from src.modules.users.repositories import UserRepository

TELEGRAM_ID_BASE = 900900900
BULK_ITEMS_COUNT = 3
PAGINATION_LIMIT = 2
PAGINATION_OFFSET = 2
PAGINATION_TOTAL_RECORDS = 5
PAGINATION_REMAINING = 3


class TestBaseRepositorySave:
    """Tests for BaseRepository.save() method."""

    async def test_save_with_dto(
        self,
        session: AsyncSession,
    ) -> None:
        """save() with DTO converts to model and saves."""
        repo = UserRepository(session)
        dto = UserCreateDTO(
            telegram_id=TELEGRAM_ID_BASE + 1,
            username="test_dto",
        )

        result = await repo.save(dto)

        assert result.id is not None
        assert result.telegram_id == TELEGRAM_ID_BASE + 1
        assert result.username == "test_dto"

    async def test_save_with_new_model(
        self,
        session: AsyncSession,
    ) -> None:
        """save() with new (not persisted) model adds and saves."""
        repo = UserRepository(session)
        model = User(
            telegram_id=TELEGRAM_ID_BASE + 2,
            username="test_model",
        )

        result = await repo.save(model)

        assert result.id is not None
        assert result.telegram_id == TELEGRAM_ID_BASE + 2
        assert result.username == "test_model"

    async def test_save_with_unmodified_model(
        self,
        session: AsyncSession,
    ) -> None:
        """save() with unmodified persisted model returns without re-adding."""
        repo = UserRepository(session)
        # First save a model
        dto = UserCreateDTO(
            telegram_id=TELEGRAM_ID_BASE + 3,
            username="original",
        )
        first_result = await repo.save(dto)

        # Get the actual model from DB
        model = await repo.get_model_by_id(first_result.id)
        assert model is not None

        # Save the unmodified model - should not re-add
        result = await repo.save(model)

        assert result.id == first_result.id
        assert result.username == "original"

    async def test_save_with_modified_model(
        self,
        session: AsyncSession,
    ) -> None:
        """save() with modified persisted model updates."""
        repo = UserRepository(session)
        # First save a model
        dto = UserCreateDTO(
            telegram_id=TELEGRAM_ID_BASE + 4,
            username="before",
        )
        first_result = await repo.save(dto)

        # Get the actual model and modify it
        model = await repo.get_model_by_id(first_result.id)
        assert model is not None
        model.username = "after"

        # Save the modified model
        result = await repo.save(model)

        assert result.id == first_result.id
        assert result.username == "after"


class TestBaseRepositorySaveBulk:
    """Tests for BaseRepository.save_bulk() method."""

    async def test_save_bulk_with_dtos(
        self,
        session: AsyncSession,
    ) -> None:
        """save_bulk() with DTOs converts and saves all."""
        repo = UserRepository(session)
        dtos = [UserCreateDTO(telegram_id=TELEGRAM_ID_BASE + 10 + i, username=f"bulk_dto_{i}") for i in range(3)]

        await repo.save_bulk(dtos)
        await session.commit()

        # Verify all were saved
        result = await repo.get_all()
        bulk_users = [u for u in result if u.username and u.username.startswith("bulk_dto_")]
        assert len(bulk_users) == BULK_ITEMS_COUNT

    async def test_save_bulk_with_new_models(
        self,
        session: AsyncSession,
    ) -> None:
        """save_bulk() with new models saves all."""
        repo = UserRepository(session)
        models = [User(telegram_id=TELEGRAM_ID_BASE + 20 + i, username=f"bulk_model_{i}") for i in range(3)]

        await repo.save_bulk(models)
        await session.commit()

        # Verify all were saved
        result = await repo.get_all()
        bulk_users = [u for u in result if u.username and u.username.startswith("bulk_model_")]
        assert len(bulk_users) == BULK_ITEMS_COUNT

    async def test_save_bulk_skips_unmodified_models(
        self,
        session: AsyncSession,
    ) -> None:
        """save_bulk() skips unmodified persisted models."""
        repo = UserRepository(session)

        # First create and persist some models
        dto = UserCreateDTO(
            telegram_id=TELEGRAM_ID_BASE + 30,
            username="existing",
        )
        saved = await repo.save(dto)
        await session.commit()

        # Get the model and include in bulk save without modification
        model = await repo.get_model_by_id(saved.id)
        assert model is not None

        # Mix unmodified model with new model
        new_model = User(telegram_id=TELEGRAM_ID_BASE + 31, username="new_in_bulk")
        await repo.save_bulk([model, new_model])
        await session.commit()

        # Verify both exist
        existing = await repo.get_by_id(saved.id)
        assert existing is not None
        assert existing.username == "existing"

        result = await repo.get_all()
        new_users = [u for u in result if u.username == "new_in_bulk"]
        assert len(new_users) == 1


class TestBaseRepositoryIsModified:
    """Tests for BaseRepository.is_modified() method."""

    async def test_is_modified_returns_true_for_new_model(
        self,
        session: AsyncSession,
    ) -> None:
        """is_modified() returns True for new (unpersisted) model."""
        repo = UserRepository(session)
        model = User(telegram_id=TELEGRAM_ID_BASE + 40)

        result = repo.is_modified(model)

        assert result is True

    async def test_is_modified_returns_false_for_unmodified(
        self,
        session: AsyncSession,
    ) -> None:
        """is_modified() returns False for clean persisted model."""
        repo = UserRepository(session)
        dto = UserCreateDTO(telegram_id=TELEGRAM_ID_BASE + 41)
        saved = await repo.save(dto)
        await session.commit()

        model = await repo.get_model_by_id(saved.id)
        assert model is not None

        result = repo.is_modified(model)

        assert result is False

    async def test_is_modified_returns_true_for_modified(
        self,
        session: AsyncSession,
    ) -> None:
        """is_modified() returns True for modified persisted model."""
        repo = UserRepository(session)
        dto = UserCreateDTO(telegram_id=TELEGRAM_ID_BASE + 42)
        saved = await repo.save(dto)
        await session.commit()

        model = await repo.get_model_by_id(saved.id)
        assert model is not None
        model.username = "changed"

        result = repo.is_modified(model)

        assert result is True


class TestBaseRepositoryGetAll:
    """Tests for BaseRepository.get_all() method."""

    async def test_get_all_returns_all_records(
        self,
        session: AsyncSession,
    ) -> None:
        """get_all() returns all records in table."""
        repo = UserRepository(session)

        # Create some records
        for i in range(BULK_ITEMS_COUNT):
            dto = UserCreateDTO(telegram_id=TELEGRAM_ID_BASE + 50 + i)
            await repo.save(dto)

        result = await repo.get_all()

        # Should have at least the 3 we created
        assert len(result) >= BULK_ITEMS_COUNT


class TestBaseRepositoryGetPaginated:
    """Tests for BaseRepository.get_paginated() method."""

    async def test_get_paginated_returns_limited_results(
        self,
        session: AsyncSession,
    ) -> None:
        """get_paginated() returns limited results with total."""
        repo = UserRepository(session)

        # Create records
        for i in range(PAGINATION_TOTAL_RECORDS):
            dto = UserCreateDTO(telegram_id=TELEGRAM_ID_BASE + 60 + i)
            await repo.save(dto)

        result = await repo.get_paginated(limit=PAGINATION_LIMIT, offset=0)

        assert len(result.items) == PAGINATION_LIMIT
        assert result.total >= PAGINATION_TOTAL_RECORDS

    async def test_get_paginated_respects_offset(
        self,
        session: AsyncSession,
    ) -> None:
        """get_paginated() respects offset parameter."""
        repo = UserRepository(session)

        # Create records
        for i in range(PAGINATION_TOTAL_RECORDS):
            dto = UserCreateDTO(telegram_id=TELEGRAM_ID_BASE + 70 + i)
            await repo.save(dto)

        result = await repo.get_paginated(limit=10, offset=PAGINATION_OFFSET)

        # Offset should skip first 2 records
        assert result.total >= PAGINATION_TOTAL_RECORDS
        assert len(result.items) >= PAGINATION_REMAINING
