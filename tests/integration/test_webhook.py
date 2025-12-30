"""Integration tests for Telegram webhook endpoint."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.bot.webhook import router

HTTP_OK = 200
HTTP_FORBIDDEN = 403
SAMPLE_UPDATE_ID = 123456789


@pytest.fixture
def test_app() -> FastAPI:
    """Create test FastAPI app with webhook router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient]:
    """Create async test client."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# Sample update data for testing
SAMPLE_UPDATE = {
    "update_id": SAMPLE_UPDATE_ID,
    "message": {
        "message_id": 1,
        "date": 1234567890,
        "chat": {"id": 123, "type": "private"},
        "from": {"id": 123, "is_bot": False, "first_name": "Test"},
        "text": "/start",
    },
}


class TestTelegramWebhook:
    """Tests for telegram_webhook endpoint."""

    async def test_webhook_rejects_invalid_secret(self, client: AsyncClient) -> None:
        """Webhook rejects request with invalid secret token."""
        with (
            patch("src.bot.webhook.settings") as mock_settings,
        ):
            mock_settings.telegram.webhook_secret.get_secret_value.return_value = "correct-secret"

            response = await client.post(
                "/telegram/webhook",
                json=SAMPLE_UPDATE,
                headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-secret"},
            )

        assert response.status_code == HTTP_FORBIDDEN
        assert "Invalid secret token" in response.json()["detail"]

    async def test_webhook_accepts_valid_secret(self, client: AsyncClient) -> None:
        """Webhook accepts request with valid secret token."""
        mock_bot = MagicMock()
        mock_dispatcher = MagicMock()
        mock_dispatcher.feed_update = AsyncMock()

        with (
            patch("src.bot.webhook.settings") as mock_settings,
            patch("src.bot.webhook.get_bot", return_value=mock_bot),
            patch("src.bot.webhook.get_dispatcher", return_value=mock_dispatcher),
        ):
            mock_settings.telegram.webhook_secret.get_secret_value.return_value = "correct-secret"

            response = await client.post(
                "/telegram/webhook",
                json=SAMPLE_UPDATE,
                headers={"X-Telegram-Bot-Api-Secret-Token": "correct-secret"},
            )

        assert response.status_code == HTTP_OK
        mock_dispatcher.feed_update.assert_called_once()

    async def test_webhook_succeeds_without_secret_configured(self, client: AsyncClient) -> None:
        """Webhook succeeds when no secret is configured."""
        mock_bot = MagicMock()
        mock_dispatcher = MagicMock()
        mock_dispatcher.feed_update = AsyncMock()

        with (
            patch("src.bot.webhook.settings") as mock_settings,
            patch("src.bot.webhook.get_bot", return_value=mock_bot),
            patch("src.bot.webhook.get_dispatcher", return_value=mock_dispatcher),
        ):
            mock_settings.telegram.webhook_secret.get_secret_value.return_value = ""

            response = await client.post(
                "/telegram/webhook",
                json=SAMPLE_UPDATE,
                # No secret header
            )

        assert response.status_code == HTTP_OK
        mock_dispatcher.feed_update.assert_called_once()

    async def test_webhook_processes_update(self, client: AsyncClient) -> None:
        """Webhook correctly processes and feeds update to dispatcher."""
        mock_bot = MagicMock()
        mock_dispatcher = MagicMock()
        mock_dispatcher.feed_update = AsyncMock()

        with (
            patch("src.bot.webhook.settings") as mock_settings,
            patch("src.bot.webhook.get_bot", return_value=mock_bot),
            patch("src.bot.webhook.get_dispatcher", return_value=mock_dispatcher),
        ):
            mock_settings.telegram.webhook_secret.get_secret_value.return_value = ""

            response = await client.post(
                "/telegram/webhook",
                json=SAMPLE_UPDATE,
            )

        assert response.status_code == HTTP_OK
        # Verify dispatcher received the update
        mock_dispatcher.feed_update.assert_called_once()
        call_args = mock_dispatcher.feed_update.call_args
        assert call_args[0][0] is mock_bot  # First arg is bot
        # Second arg is the Update object
        update = call_args[0][1]
        assert update.update_id == SAMPLE_UPDATE_ID
