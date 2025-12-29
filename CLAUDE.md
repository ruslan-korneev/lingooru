# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Lingooru** — Telegram-бот для изучения языков с интервальным повторением, голосовым вводом и AI-проверкой.

### Цель
Помочь пользователям эффективно изучать иностранные языки через Telegram.

### Ключевые фичи
- **Spaced Repetition (SM-2)** — интервальное повторение как в Anki
- **Голосовой ввод** — практика произношения через Whisper + LLM
- **AI-задания** — генерация и проверка заданий через Claude/GPT
- **Учитель-ученик** — система для преподавателей с журналом

### Языки
- **Изучения**: EN→RU, KO→RU
- **Интерфейса бота**: Русский, English, 한국어

### Документация
- **Roadmap и архитектура**: `docs/ROADMAP.md`

---

## Commands

```bash
# Setup environment
uv venv && source .venv/bin/activate
uv sync --all-groups

# Run all quality checks
make              # fmt, lint, db, test
make ci           # Full CI pipeline (sync, fmt, lint, upgrade-db, db, test)

# Individual commands
make fmt          # Format with ruff
make lint         # Lint with ruff and mypy (strict mode)
make test         # Run pytest with coverage
make db           # Validate alembic migrations match models
make upgrade-db   # Apply all migrations

# Run tests by category
uv run pytest -k unit -v           # Unit tests only
uv run pytest -k integration -v    # Integration tests only
uv run pytest -k "not benchmark"   # Exclude benchmarks

# Run specific tests
uv run pytest tests/unit/modules/users/test_services.py -v
uv run pytest -k "test_name" -v

# Database migrations
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"
uv run alembic downgrade -1

# API Server
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

## Architecture

### Tech Stack
- **Backend**: Python 3.12+, FastAPI, SQLAlchemy 2.0 (async), PostgreSQL
- **Telegram**: aiogram 3.x
- **AI/ML**: OpenAI (GPT-4o, Whisper), Claude (Anthropic)
- **Audio**: Forvo API, Google TTS (fallback)

### Telegram Bot Structure

```
src/bot/
├── __init__.py
├── dispatcher.py          # aiogram Dispatcher setup
├── handlers/              # Message and callback handlers
│   ├── start.py           # /start command
│   ├── menu.py            # Main menu navigation
│   ├── learn.py           # Learning flow
│   ├── review.py          # SM-2 review sessions
│   ├── settings.py        # User settings
│   └── voice.py           # Voice message processing
├── keyboards/             # Keyboard builders
│   ├── reply.py           # Persistent reply keyboard
│   ├── menu.py            # Menu inline keyboards
│   ├── learn.py           # Learning keyboards
│   └── settings.py        # Settings keyboards
├── locales/               # i18n translations
│   ├── ru.yaml
│   ├── en.yaml
│   └── ko.yaml
├── middleware/            # aiogram middleware
│   ├── i18n.py            # Localization
│   └── user.py            # User loading from DB
└── filters/               # Custom filters
```

### Bot UX Principles
- **Минимум команд** — только `/start`
- **Inline Keyboards** — основная навигация в сообщениях
- **Reply Keyboard** — `[📚 Учить] [🔄 Повторять] [📋 Меню]` всегда видна
- **Edit Message** — обновление сообщения вместо нового

### Callback Data Schema
```
menu:main              → Main menu
learn:start            → Start learning
learn:know/hard/forgot → Rate word (SM-2 quality)
review:start           → Start review session
review:show            → Show answer
review:rate:{1-5}      → Rate recall quality
settings:lang:{code}   → Change UI language
settings:pair:{pair}   → Change language pair
```

### Planned Modules

| Module | Description |
|--------|-------------|
| `users` | User management, ui_language, language_pair, notifications |
| `vocabulary` | Words, translations, user dictionary |
| `srs` | SM-2 algorithm, Review, ReviewLog |
| `voice` | Whisper transcription, pronunciation checking |
| `stats` | Statistics, achievements, referrals |
| `teaching` | Teacher-student system, assignments, journal |

---

### API Versioning

All API endpoints are prefixed with `/v1/`. Register new routers on `v1_router`:

```python
# src/core/api/routers.py
from src.modules.my_module import router as my_router
v1_router.include_router(my_router)
```

### Dependency Injection Pattern

Routes use `dependency-injector` with the `@inject` decorator:

```python
from dependency_injector.wiring import Provide, inject
from src.core.dependencies.containers import Container
from src.db.session import AsyncSessionMaker

@router.get("/{id}")
@inject
async def get_item(
    id: UUID,
    db_session_maker: Annotated[AsyncSessionMaker, Depends(Provide[Container.db_session_maker])],
) -> ItemReadDTO:
    async with db_session_maker as session:
        service = ItemService(session)
        # ... use service
        await session.commit()  # Required for write operations
```

The container is defined in `src/core/dependencies/containers.py` and wired to all packages in `src`.

### Module Structure

Each feature module in `src/modules/` follows:
- `models.py` - SQLAlchemy model extending `SAModel`
- `dto.py` - Pydantic DTOs extending `BaseDTO` (Create/Read/Update variants)
- `repositories.py` - Data access extending `BaseRepository[Model, CreateDTO, ReadDTO]`
- `services.py` - Business logic, takes `AsyncSession` in constructor
- `routers.py` - FastAPI routes with `@inject` decorator

### Key Base Classes

**BaseRepository** (`src/core/types/repositories.py`):
- Generic `[Model, CreateDTO, ReadDTO]` type parameters
- Provides `get_all()`, `get_paginated()`, `save()`, `save_bulk()`
- Extend for custom queries

**PaginatedResponse** (`src/core/types/dto.py`):
- Generic wrapper for paginated list responses
- Fields: `items`, `total`, `limit`, `offset`, `has_more`
- Use `PaginatedResponse.create()` factory method

**BaseDTO** (`src/core/types/dto.py`):
- `from_attributes=True` for ORM compatibility
- `populate_by_name=True` for alias support

**SAModel** (`src/db/base.py`):
- PostgreSQL naming conventions for constraints/indexes
- Type annotation mapping for `datetime` (timezone-aware) and `uuid.UUID`

### Custom Exceptions

Use exceptions from `src/core/exceptions.py` for consistent error handling:

```python
from src.core.exceptions import NotFoundError, ConflictError, AppError

# Raise in service/router layer
raise NotFoundError("User not found")
raise ConflictError("Email already exists")

# Custom exception with extra data
raise AppError("Custom error", user_id=user_id)
```

Available exceptions: `AppError`, `NotFoundError`, `ConflictError`, `ValidationError`, `RateLimitExceededError`

### Middleware

**Request ID** (`src/core/middleware/request_id.py`):
- Generates UUID for each request
- Available via `request.state.request_id`
- Automatically included in logs via loguru context
- Returned in `X-Request-ID` response header

**Rate Limiting** (`src/core/middleware/rate_limit.py`):
- Token bucket algorithm
- Per-IP limiting
- Configurable via `RATE_LIMIT__*` env vars
- Returns `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers

### Adding a New Module

1. Create `src/modules/<name>/` with models, dto, repositories, services, routers
2. Export router in `__init__.py`
3. Register in `src/core/api/routers.py`: `v1_router.include_router(my_router)`
4. Create migration: `uv run alembic revision --autogenerate -m "add_table"`
5. Add tests in `tests/unit/modules/<name>/` and `tests/integration/`

### Testing Structure

```
tests/
  conftest.py              # Common fixtures (session, api_client, etc.)
  mimic/                   # Test doubles (stubs, fakes, mocks)
    session.py             # FakeSessionMaker
  benchmark/               # Performance tests
  integration/             # API endpoint tests, database tests
  unit/                    # Unit tests
    modules/
      users/
        test_services.py
        test_repositories.py
        test_routers.py    # Router handler unit tests
```

Key fixtures in `tests/conftest.py`:
- `session` - AsyncSession for database operations
- `api_client` - ASGI test client for endpoint testing
- `user_service`, `user_repository` - Pre-configured instances
- `sample_user`, `second_sample_user` - Test user fixtures

Tests use transaction rollback - each test runs in a transaction that rolls back automatically.

## Configuration

Settings are in `src/config.py` using Pydantic BaseSettings with nested models:
- `DbSettings` - Database connection
- `SentrySettings` - Error tracking
- `CORSSettings` - CORS configuration
- `RateLimitSettings` - Rate limiting

Environment variables use `__` as nested delimiter (e.g., `CORS__ALLOW_ORIGINS`).

## Important Notes

### General
- **UV Package Manager**: Always use `uv run` for commands
- **Type Safety**: Strict mypy - all code must be fully typed
- **Session Commits**: Write operations require explicit `await session.commit()`
- **Async Throughout**: All database operations and API calls must be async
- **API Versioning**: All endpoints are under `/v1/` prefix
- **Error Handling**: Use custom exceptions from `src/core/exceptions.py`
- **Pagination**: List endpoints return `PaginatedResponse` with `limit`/`offset` query params

### Telegram Bot
- **aiogram 3.x**: Use Dispatcher, Router, callback_query handlers
- **Inline Keyboards**: Primary navigation, use `InlineKeyboardBuilder`
- **Reply Keyboard**: Persistent buttons under input field
- **Edit vs Send**: Prefer `message.edit_text()` over sending new messages
- **Callback Data**: Use format `action:param` (e.g., `learn:start`, `review:rate:5`)
- **i18n**: All user-facing strings through localization files
- **User Context**: Load user in middleware, access via `message.from_user.id`

### AI Integration
- **OpenAI**: GPT-4o for task generation/checking, Whisper for transcription
- **Claude**: Alternative LLM for task generation/checking
- **Audio**: Forvo API for native pronunciation, Google TTS as fallback
- **Prompts**: Store LLM prompts in `src/bot/prompts/` or constants
