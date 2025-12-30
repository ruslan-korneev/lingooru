"""Tests for core ASGI application setup."""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import Request
from fastapi.exceptions import RequestValidationError

from src.core.asgi import (
    _build_error_response,
    _get_request_id,
    app_exception_handler,
    generic_exception_handler,
    get_app,
    lifespan,
    validation_exception_handler,
)
from src.core.exceptions import AppError, NotFoundError

HTTP_NOT_FOUND = 404
HTTP_UNPROCESSABLE = 422
HTTP_SERVER_ERROR = 500


class TestGetRequestId:
    """Tests for _get_request_id helper."""

    def test_returns_request_id_when_present(self) -> None:
        """Returns request_id from request state."""
        request = MagicMock(spec=Request)
        request.state.request_id = "test-uuid-123"

        result = _get_request_id(request)

        assert result == "test-uuid-123"

    def test_returns_none_when_missing(self) -> None:
        """Returns None when request_id is not in state."""
        request = MagicMock(spec=Request)
        # Remove request_id attribute
        del request.state.request_id

        result = _get_request_id(request)

        assert result is None


class TestBuildErrorResponse:
    """Tests for _build_error_response helper."""

    def test_builds_basic_response(self) -> None:
        """Builds response with error and detail."""
        result = _build_error_response(
            error="TestError",
            detail="Test detail message",
            request_id=None,
        )

        assert result == {
            "error": "TestError",
            "detail": "Test detail message",
        }

    def test_includes_request_id_when_provided(self) -> None:
        """Includes request_id when provided."""
        result = _build_error_response(
            error="TestError",
            detail="Test detail",
            request_id="req-123",
        )

        assert result == {
            "error": "TestError",
            "detail": "Test detail",
            "request_id": "req-123",
        }

    def test_includes_extra_when_provided(self) -> None:
        """Includes extra data when provided."""
        result = _build_error_response(
            error="TestError",
            detail="Test detail",
            request_id=None,
            extra={"field": "value"},
        )

        assert result == {
            "error": "TestError",
            "detail": "Test detail",
            "extra": {"field": "value"},
        }

    def test_includes_both_request_id_and_extra(self) -> None:
        """Includes both request_id and extra when provided."""
        result = _build_error_response(
            error="TestError",
            detail="Test detail",
            request_id="req-456",
            extra={"key": "data"},
        )

        assert result == {
            "error": "TestError",
            "detail": "Test detail",
            "request_id": "req-456",
            "extra": {"key": "data"},
        }


class TestAppExceptionHandler:
    """Tests for app_exception_handler."""

    async def test_handles_app_error(self) -> None:
        """Handles AppError with correct status code."""
        request = MagicMock(spec=Request)
        request.state.request_id = "req-123"
        exc = NotFoundError("Resource not found")

        response = await app_exception_handler(request, exc)

        assert response.status_code == HTTP_NOT_FOUND
        assert b"NotFoundError" in response.body
        assert b"Resource not found" in response.body

    async def test_handles_app_error_with_extra(self) -> None:
        """Handles AppError with extra data."""
        request = MagicMock(spec=Request)
        del request.state.request_id
        exc = AppError("Custom error", user_id="123")

        response = await app_exception_handler(request, exc)

        assert response.status_code == HTTP_SERVER_ERROR  # AppError defaults to 500
        assert b"AppError" in response.body
        assert b"user_id" in response.body


class TestValidationExceptionHandler:
    """Tests for validation_exception_handler."""

    async def test_handles_validation_error(self) -> None:
        """Handles RequestValidationError."""
        request = MagicMock(spec=Request)
        request.state.request_id = "req-789"

        # Create a validation error
        exc = RequestValidationError(errors=[{"loc": ["body", "field"], "msg": "required"}])

        response = await validation_exception_handler(request, exc)

        assert response.status_code == HTTP_UNPROCESSABLE
        assert b"ValidationError" in response.body
        assert b"Request validation failed" in response.body


class TestGenericExceptionHandler:
    """Tests for generic_exception_handler."""

    async def test_handles_generic_exception(self) -> None:
        """Handles unexpected exceptions."""
        request = MagicMock(spec=Request)
        request.state.request_id = "req-000"
        exc = RuntimeError("Something went wrong")

        response = await generic_exception_handler(request, exc)

        assert response.status_code == HTTP_SERVER_ERROR
        assert b"InternalServerError" in response.body
        assert b"An unexpected error occurred" in response.body


class TestLifespan:
    """Tests for lifespan context manager."""

    async def test_lifespan_without_bot_token(self) -> None:
        """Lifespan does nothing when bot token is empty."""
        app = MagicMock()

        with patch("src.core.asgi.settings") as mock_settings:
            mock_settings.telegram.bot_token.get_secret_value.return_value = ""

            async with lifespan(app):
                pass

        # No bot operations should have been called

    async def test_lifespan_with_bot_token_no_webhook(self) -> None:
        """Lifespan creates bot but doesn't set webhook when webhook_url is empty."""
        app = MagicMock()
        mock_bot = AsyncMock()

        with (
            patch("src.core.asgi.settings") as mock_settings,
            patch("src.bot.dispatcher.get_bot", return_value=mock_bot),
        ):
            mock_settings.telegram.bot_token.get_secret_value.return_value = "test-token"
            mock_settings.telegram.webhook_url = ""

            async with lifespan(app):
                pass

            mock_bot.set_webhook.assert_not_called()
            mock_bot.session.close.assert_called_once()

    async def test_lifespan_with_webhook(self) -> None:
        """Lifespan sets and deletes webhook when webhook_url is provided."""
        app = MagicMock()
        mock_bot = AsyncMock()

        with (
            patch("src.core.asgi.settings") as mock_settings,
            patch("src.bot.dispatcher.get_bot", return_value=mock_bot),
        ):
            mock_settings.telegram.bot_token.get_secret_value.return_value = "test-token"
            mock_settings.telegram.webhook_url = "https://example.com"
            mock_settings.telegram.webhook_secret.get_secret_value.return_value = "secret"

            async with lifespan(app):
                mock_bot.set_webhook.assert_called_once()

            mock_bot.delete_webhook.assert_called_once()
            mock_bot.session.close.assert_called_once()

    async def test_lifespan_webhook_without_secret(self) -> None:
        """Lifespan sets webhook without secret token when secret is empty."""
        app = MagicMock()
        mock_bot = AsyncMock()

        with (
            patch("src.core.asgi.settings") as mock_settings,
            patch("src.bot.dispatcher.get_bot", return_value=mock_bot),
        ):
            mock_settings.telegram.bot_token.get_secret_value.return_value = "test-token"
            mock_settings.telegram.webhook_url = "https://example.com"
            mock_settings.telegram.webhook_secret.get_secret_value.return_value = ""

            async with lifespan(app):
                call_args = mock_bot.set_webhook.call_args
                assert call_args.kwargs["secret_token"] is None


class TestGetApp:
    """Tests for get_app factory."""

    def test_creates_app_without_sentry(self) -> None:
        """Creates app without Sentry when DSN is empty."""
        with (
            patch("src.core.asgi.settings") as mock_settings,
            patch("src.core.asgi.sentry_init") as mock_sentry_init,
            patch("src.core.asgi.Container"),
        ):
            mock_settings.sentry.dsn.get_secret_value.return_value = ""
            mock_settings.project_title = "Test"
            mock_settings.project_description = "Test app"
            mock_settings.cors.allow_origins = ["*"]
            mock_settings.cors.allow_origin_regex = None
            mock_settings.cors.allow_credentials = True
            mock_settings.cors.allow_methods = ["*"]
            mock_settings.cors.allow_headers = ["*"]
            mock_settings.cors.expose_headers = []
            mock_settings.cors.max_age = 600
            mock_settings.rate_limit.enabled = False

            app = get_app()

            mock_sentry_init.assert_not_called()
            assert app.title == "Test"

    def test_creates_app_with_sentry(self) -> None:
        """Creates app with Sentry when DSN is provided."""
        with (
            patch("src.core.asgi.settings") as mock_settings,
            patch("src.core.asgi.sentry_init") as mock_sentry_init,
            patch("src.core.asgi.Container"),
        ):
            mock_settings.sentry.dsn.get_secret_value.return_value = "https://sentry.io/123"
            mock_settings.environment = "test"
            mock_settings.sentry.enable_tracing = True
            mock_settings.sentry.traces_sample_rate = 1.0
            mock_settings.sentry.profiles_sample_rate = 1.0
            mock_settings.project_title = "Test"
            mock_settings.project_description = "Test app"
            mock_settings.cors.allow_origins = ["*"]
            mock_settings.cors.allow_origin_regex = None
            mock_settings.cors.allow_credentials = True
            mock_settings.cors.allow_methods = ["*"]
            mock_settings.cors.allow_headers = ["*"]
            mock_settings.cors.expose_headers = []
            mock_settings.cors.max_age = 600
            mock_settings.rate_limit.enabled = False

            app = get_app()

            mock_sentry_init.assert_called_once()
            assert app.title == "Test"

    def test_creates_app_with_rate_limiting(self) -> None:
        """Creates app with rate limiting when enabled."""
        with (
            patch("src.core.asgi.settings") as mock_settings,
            patch("src.core.asgi.Container"),
            patch("src.core.asgi.InMemoryRateLimiter") as mock_limiter_class,
            patch("src.core.asgi.RateLimitMiddleware"),
        ):
            mock_settings.sentry.dsn.get_secret_value.return_value = ""
            mock_settings.project_title = "Test"
            mock_settings.project_description = "Test app"
            mock_settings.cors.allow_origins = ["*"]
            mock_settings.cors.allow_origin_regex = None
            mock_settings.cors.allow_credentials = True
            mock_settings.cors.allow_methods = ["*"]
            mock_settings.cors.allow_headers = ["*"]
            mock_settings.cors.expose_headers = []
            mock_settings.cors.max_age = 600
            mock_settings.rate_limit.enabled = True
            mock_settings.rate_limit.requests_per_minute = 60
            mock_settings.rate_limit.burst_size = 10

            get_app()

            mock_limiter_class.assert_called_once_with(
                requests_per_minute=60,
                burst_size=10,
            )
