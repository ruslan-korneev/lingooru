# Lingooru

[![CI](https://github.com/ruslan-korneev/lingooru/actions/workflows/ci.yml/badge.svg)](https://github.com/ruslan-korneev/lingooru/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/ruslan-korneev/lingooru/graph/badge.svg?token=j2IsTFTXxu)](https://codecov.io/gh/ruslan-korneev/lingooru)

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![aiogram 3.x](https://img.shields.io/badge/aiogram-3.x-blue.svg)](https://aiogram.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![mypy](https://img.shields.io/badge/mypy-strict-blue.svg)](http://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Telegram bot for language learning with spaced repetition, voice practice, and AI-powered feedback.

## Features

### Learning
- **Vocabulary Management** - Add words manually or from curated word lists
- **Spaced Repetition (SM-2)** - Anki-like algorithm for optimal memorization
- **Multi-language Support** - English and Korean learning with Russian interface

### Practice
- **Voice Pronunciation** - Record voice messages, get AI feedback via OpenAI Whisper
- **Audio Playback** - Listen to word pronunciations (gTTS with S3/MinIO caching)
- **Review Sessions** - Track progress with quality ratings

### Technical
- **aiogram 3.x** - Modern async Telegram bot framework
- **FastAPI** - REST API with async support
- **SQLAlchemy 2.0** - Async ORM with PostgreSQL
- **i18n** - Localized interface (Russian, English, Korean)

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- PostgreSQL 17+
- Docker (for MinIO)

## Quick Start

### 1. Setup Environment

```bash
# Clone and enter project
cd lingooru

# Create and activate virtual environment
uv venv && source .venv/bin/activate
uv sync --all-groups
```

### 2. Configure

```bash
# Copy example config
cp .env.example .env

# Edit with your credentials
$EDITOR .env
```

Required settings:
```env
# Database
DB__HOST=localhost
DB__PORT=5432
DB__NAME=lingooru
DB__USERNAME=postgres
DB__PASSWORD=postgres

# Telegram
telegram__bot_token=YOUR_BOT_TOKEN

# OpenAI (for voice recognition)
openai__api_key=YOUR_OPENAI_KEY

# S3/MinIO (for audio caching)
S3__ENDPOINT_URL=http://localhost:9000
S3__ACCESS_KEY=minioadmin
S3__SECRET_KEY=minioadmin
S3__BUCKET_NAME=lingooru-audio
```

### 3. Start Services

```bash
# Start MinIO for audio storage
docker run -d \
  --name minio \
  -p 9000:9000 \
  -p 9001:9001 \
  -v ~/minio/data:/data \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"

# Create bucket
docker exec minio mc alias set local http://localhost:9000 minioadmin minioadmin
docker exec minio mc mb local/lingooru-audio --ignore-existing
docker exec minio mc anonymous set download local/lingooru-audio
```

### 4. Run Migrations

```bash
uv run alembic upgrade head
```

### 5. Start Bot

```bash
# Run Telegram bot
make bot

# Or run API server
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

## Bot Commands

The bot uses inline keyboards for navigation. Main features:

| Button | Description |
|--------|-------------|
| 📚 Учить | Learn new words |
| 🔄 Повторять | Review due words (spaced repetition) |
| 🎤 Произношение | Practice pronunciation with voice |
| 📋 Меню | Main menu with stats |

### Learning Flow

1. **Add Words** - From word lists or manually
2. **Learn** - See word, translation, example; rate as Know/Hard/Forgot
3. **Review** - Spaced repetition based on SM-2 algorithm
4. **Voice Practice** - Record pronunciation, get AI feedback

## Development

### Code Quality

```bash
make              # Run all checks (fmt, lint, db, test)
make fmt          # Format code with ruff
make lint         # Lint with ruff and mypy (strict)
make test         # Run pytest with coverage
make db           # Validate migrations
```

### Project Structure

```
src/
├── bot/                    # Telegram bot
│   ├── handlers/           # Message & callback handlers
│   ├── keyboards/          # Inline & reply keyboards
│   ├── locales/            # i18n translations (ru, en, ko)
│   └── middleware/         # User loading, i18n
├── modules/
│   ├── audio/              # TTS generation & S3 storage
│   ├── srs/                # Spaced repetition (SM-2)
│   ├── users/              # User management
│   ├── vocabulary/         # Words, translations, user dictionary
│   └── voice/              # Voice transcription & feedback
├── core/                   # API core (routes, middleware, DI)
├── db/                     # Database config & sessions
└── config.py               # Application settings

tests/
├── unit/                   # Unit tests
├── integration/            # API & database tests
└── conftest.py             # Shared fixtures
```

### Adding Features

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines.

## Testing

```bash
# Run all tests
make test

# Run by category
uv run pytest -k unit -v
uv run pytest -k integration -v

# Run specific module
uv run pytest tests/unit/modules/audio/ -v
```

Coverage requirements: 80% line, 70% branch.

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DB__*` | PostgreSQL connection | localhost:5432 |
| `telegram__bot_token` | Telegram bot token | - |
| `openai__api_key` | OpenAI API key | - |
| `S3__ENDPOINT_URL` | MinIO/S3 endpoint | http://localhost:9000 |
| `S3__ACCESS_KEY` | S3 access key | - |
| `S3__SECRET_KEY` | S3 secret key | - |
| `S3__BUCKET_NAME` | Audio bucket name | lingooru-audio |
| `LOGGING_LEVEL` | Log level | INFO |

## License

MIT
