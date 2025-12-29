import asyncio
from collections.abc import AsyncGenerator, Generator
from contextlib import suppress
from typing import TYPE_CHECKING

import alembic
import alembic.command
import alembic.config
import asyncpg
import pytest
import pytest_asyncio
from _pytest.monkeypatch import MonkeyPatch
from httpx import ASGITransport, AsyncClient
from pytest_httpx import HTTPXMock
from sqlalchemy import Connection
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, create_async_engine

from src.config import settings
from src.core.asgi import get_app
from src.modules.srs.repositories import ReviewLogRepository, ReviewRepository
from src.modules.srs.services import SRSService
from src.modules.users.dto import UserCreateDTO, UserReadDTO
from src.modules.users.repositories import UserRepository
from src.modules.users.services import UserService
from src.modules.vocabulary.dto import (
    TranslationCreateDTO,
    TranslationReadDTO,
    WordCreateDTO,
    WordReadDTO,
)
from src.modules.vocabulary.models import Language
from src.modules.vocabulary.repositories import (
    TranslationRepository,
    UserWordRepository,
    WordRepository,
)
from src.modules.vocabulary.services import VocabularyService
from tests.mimic.session import FakeSessionMaker

if TYPE_CHECKING:
    from src.core.asgi import FastAPIWrapper


@pytest.fixture(scope="session")
def monkey_session() -> Generator[MonkeyPatch]:
    mp = MonkeyPatch()
    yield mp
    mp.undo()


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        loop.close()


@pytest.fixture(scope="session")
def postgres_test_db_name(request: pytest.FixtureRequest) -> str:
    db_name = f"test-{settings.db.name}"
    xdist_suffix = getattr(request.config, "workerinput", {}).get("workerid")
    if xdist_suffix:  # NOTE: Put a suffix like _gw0, _gw1 etc on xdist processes
        db_name += f"_{xdist_suffix}"
    return db_name


@pytest.fixture(scope="session")
def postgres_test_db_url(postgres_test_db_name: str) -> str:
    return settings.db.get_url(scheme="postgresql+asyncpg", db_name=postgres_test_db_name).get_secret_value()


async def _create_test_db_if_not_exists(db_name: str) -> None:
    dsn = settings.db.get_url(scheme="postgresql", db_name=db_name).get_secret_value()
    try:
        await asyncpg.connect(dsn=dsn)
    except asyncpg.InvalidCatalogNameError:  # Database does not exist, create it.
        with suppress(asyncpg.exceptions.DuplicateDatabaseError):
            dsn = settings.db.get_url(scheme="postgresql").get_secret_value()
            sys_conn = await asyncpg.connect(dsn)
            await sys_conn.execute(f'CREATE DATABASE "{db_name}"')
            await sys_conn.close()


async def _delete_test_db_if_exists(db_name: str) -> None:
    dsn = settings.db.get_url(scheme="postgresql").get_secret_value()
    sys_conn = await asyncpg.connect(dsn)

    # Check if database exists before trying to delete it
    result = await sys_conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", db_name)

    if result:
        await sys_conn.execute(
            "SELECT pg_terminate_backend(pg_stat_activity.pid) "  # noqa: S608
            f"FROM pg_stat_activity WHERE pg_stat_activity.datname = '{db_name}'",
        )
        await sys_conn.execute(f'DROP DATABASE "{db_name}"')

    await sys_conn.close()


@pytest.fixture(scope="session", autouse=True)
async def create_test_db_if_not_exists(postgres_test_db_name: str) -> AsyncGenerator[None]:
    await _create_test_db_if_not_exists(postgres_test_db_name)
    yield
    await _delete_test_db_if_exists(postgres_test_db_name)


@pytest_asyncio.fixture(scope="session")
async def connection(postgres_test_db_url: str) -> AsyncGenerator[AsyncConnection]:
    engine = create_async_engine(url=postgres_test_db_url, pool_pre_ping=True)
    async with engine.connect() as conn:
        yield conn


@pytest_asyncio.fixture(scope="session")
async def alembic_config(postgres_test_db_url: str) -> alembic.config.Config:
    config = alembic.config.Config(settings.root_dir / "alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_test_db_url)
    return config


def _upgrade_database(connection: Connection, alembic_config: alembic.config.Config) -> None:
    alembic_config.attributes["connection"] = connection
    alembic.command.upgrade(config=alembic_config, revision="head")


@pytest_asyncio.fixture(scope="session", autouse=True)
async def migrate_database(connection: AsyncConnection, alembic_config: alembic.config.Config) -> None:
    await connection.run_sync(_upgrade_database, alembic_config)


@pytest_asyncio.fixture(autouse=True)
async def wrap_tests_with_transaction(migrate_database: None, connection: AsyncConnection) -> AsyncGenerator[None]:
    _ = migrate_database
    transaction = connection
    await transaction.begin()

    yield

    await transaction.rollback()


@pytest.fixture
async def session(connection: AsyncConnection) -> AsyncGenerator[AsyncSession]:
    async with AsyncSession(bind=connection) as session:
        yield session


@pytest.fixture
async def httpx_client(httpx_mock: HTTPXMock) -> AsyncGenerator[AsyncClient]:
    _ = httpx_mock
    async with AsyncClient() as client:
        yield client


@pytest.fixture
def test_app(session: AsyncSession) -> "FastAPIWrapper":
    """Create app with overridden db_session_maker for test isolation."""
    app = get_app()
    app.container.db_session_maker.override(FakeSessionMaker(session))
    return app


@pytest.fixture
async def api_client(test_app: "FastAPIWrapper") -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://0.0.0.0/") as client:
        yield client
    test_app.container.db_session_maker.reset_override()


# Module fixtures - Users


@pytest.fixture
def user_repository(session: AsyncSession) -> UserRepository:
    return UserRepository(session)


@pytest.fixture
def user_service(session: AsyncSession) -> UserService:
    return UserService(session)


@pytest_asyncio.fixture
async def sample_user(session: AsyncSession, user_service: UserService) -> UserReadDTO:
    dto = UserCreateDTO(
        telegram_id=123456789,
        username="testuser",
        first_name="Test User",
    )
    user, _ = await user_service.get_or_create(dto)
    await session.flush()
    return user


@pytest_asyncio.fixture
async def second_sample_user(session: AsyncSession, user_service: UserService) -> UserReadDTO:
    dto = UserCreateDTO(
        telegram_id=987654321,
        username="seconduser",
        first_name="Second User",
    )
    user, _ = await user_service.get_or_create(dto)
    await session.flush()
    return user


# Module fixtures - Vocabulary


@pytest.fixture
def word_repository(session: AsyncSession) -> WordRepository:
    return WordRepository(session)


@pytest.fixture
def translation_repository(session: AsyncSession) -> TranslationRepository:
    return TranslationRepository(session)


@pytest.fixture
def user_word_repository(session: AsyncSession) -> UserWordRepository:
    return UserWordRepository(session)


@pytest.fixture
def vocabulary_service(session: AsyncSession) -> VocabularyService:
    return VocabularyService(session)


@pytest_asyncio.fixture
async def sample_word(session: AsyncSession, word_repository: WordRepository) -> WordReadDTO:
    """Create a sample word fixture."""
    dto = WordCreateDTO(
        text="hello",
        language=Language.EN,
        phonetic="/həˈloʊ/",  # noqa: RUF001
        audio_url="https://example.com/hello.mp3",
    )
    word = await word_repository.save(dto)
    await session.flush()
    return word


@pytest_asyncio.fixture
async def sample_word_with_translation(
    session: AsyncSession,
    word_repository: WordRepository,
    translation_repository: TranslationRepository,
) -> tuple[WordReadDTO, TranslationReadDTO]:
    """Create a sample word with translation fixture."""
    word_dto = WordCreateDTO(
        text="world",
        language=Language.EN,
        phonetic="/wɜːrld/",  # noqa: RUF001
    )
    word = await word_repository.save(word_dto)

    trans_dto = TranslationCreateDTO(
        word_id=word.id,
        translated_text="мир",
        target_language=Language.RU,
        example_sentence="Hello, world!",
    )
    translation = await translation_repository.save(trans_dto)
    await session.flush()
    return word, translation


# Module fixtures - SRS


@pytest.fixture
def review_repository(session: AsyncSession) -> ReviewRepository:
    return ReviewRepository(session)


@pytest.fixture
def review_log_repository(session: AsyncSession) -> ReviewLogRepository:
    return ReviewLogRepository(session)


@pytest.fixture
def srs_service(session: AsyncSession) -> SRSService:
    return SRSService(session)
