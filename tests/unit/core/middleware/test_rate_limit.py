"""Tests for rate limiting middleware."""

from typing import Any, TypedDict, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.requests import Request
from starlette.responses import Response

from src.core.middleware.rate_limit import InMemoryRateLimiter, RateLimitMiddleware


class RequestScope(TypedDict):
    """Typed dict for ASGI request scope."""

    type: str
    path: str
    headers: list[tuple[bytes, bytes]]
    client: tuple[str, int] | None


class TestInMemoryRateLimiter:
    """Tests for the token bucket rate limiter."""

    def test_first_request_allowed(self) -> None:
        """First request from a client should always be allowed."""
        limiter = InMemoryRateLimiter(requests_per_minute=60, burst_size=10)

        allowed, headers = limiter.is_allowed("client_1")

        assert allowed is True
        assert headers["X-RateLimit-Limit"] == "10"
        assert headers["X-RateLimit-Remaining"] == "9"

    def test_burst_requests_allowed(self) -> None:
        """Multiple requests within burst size should be allowed."""
        limiter = InMemoryRateLimiter(requests_per_minute=60, burst_size=5)

        for i in range(5):
            allowed, headers = limiter.is_allowed("client_burst")
            assert allowed is True
            assert headers["X-RateLimit-Remaining"] == str(5 - i - 1)

    def test_rate_limit_exceeded(self) -> None:
        """Requests beyond burst size should be denied."""
        limiter = InMemoryRateLimiter(requests_per_minute=60, burst_size=3)

        # Use all tokens
        for _ in range(3):
            allowed, _ = limiter.is_allowed("client_limited")
            assert allowed is True

        # Next request should be denied
        allowed, headers = limiter.is_allowed("client_limited")

        assert allowed is False
        assert "Retry-After" in headers
        assert headers["X-RateLimit-Remaining"] == "0"

    def test_token_replenishment(self) -> None:
        """Tokens should replenish over time."""
        # 60 requests per minute = 1 token per second
        limiter = InMemoryRateLimiter(requests_per_minute=60, burst_size=2)

        # Use all tokens
        limiter.is_allowed("client_replenish")
        limiter.is_allowed("client_replenish")

        # Manually advance the last_update time to simulate time passing
        bucket = limiter._buckets["client_replenish"]  # noqa: SLF001
        bucket.last_update -= 2  # Simulate 2 seconds passing

        # Now should have tokens again
        allowed, headers = limiter.is_allowed("client_replenish")

        assert allowed is True
        # Should have replenished ~2 tokens, used 1, so remaining should be ~1
        assert int(headers["X-RateLimit-Remaining"]) >= 0

    def test_different_clients_independent(self) -> None:
        """Different clients should have independent limits."""
        limiter = InMemoryRateLimiter(requests_per_minute=60, burst_size=2)

        # Exhaust client_a
        limiter.is_allowed("client_a")
        limiter.is_allowed("client_a")
        allowed_a, _ = limiter.is_allowed("client_a")

        # client_b should still be allowed
        allowed_b, _ = limiter.is_allowed("client_b")

        assert allowed_a is False
        assert allowed_b is True


class TestRateLimitMiddleware:
    """Tests for the rate limit middleware."""

    @pytest.fixture
    def limiter(self) -> InMemoryRateLimiter:
        return InMemoryRateLimiter(requests_per_minute=60, burst_size=10)

    @pytest.fixture
    def middleware(self, limiter: InMemoryRateLimiter) -> RateLimitMiddleware:
        app = MagicMock()
        return RateLimitMiddleware(app, limiter)

    def _create_request(
        self,
        path: str = "/test",
        client_host: str = "127.0.0.1",
        headers: dict[str, str] | None = None,
    ) -> Request:
        """Create a mock Request object."""
        scope = {
            "type": "http",
            "path": path,
            "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
            "client": (client_host, 12345) if client_host else None,
        }
        return Request(scope)

    async def test_excluded_paths_bypass_limit(
        self,
        middleware: RateLimitMiddleware,
    ) -> None:
        """Health check endpoints should bypass rate limiting."""
        request = self._create_request(path="/health")
        call_next = AsyncMock(return_value=Response())

        response = await middleware.dispatch(request, call_next)

        call_next.assert_called_once_with(request)
        assert response.status_code == 200  # noqa: PLR2004

    async def test_v1_health_excluded(
        self,
        middleware: RateLimitMiddleware,
    ) -> None:
        """v1 health endpoint should bypass rate limiting."""
        request = self._create_request(path="/v1/health")
        call_next = AsyncMock(return_value=Response())

        await middleware.dispatch(request, call_next)

        call_next.assert_called_once_with(request)

    async def test_rate_limited_returns_429(
        self,
    ) -> None:
        """Rate limited requests should return 429."""
        # Create middleware with small burst
        small_limiter = InMemoryRateLimiter(requests_per_minute=60, burst_size=1)
        app = MagicMock()
        middleware = RateLimitMiddleware(app, small_limiter)
        call_next = AsyncMock(return_value=Response())

        request = self._create_request()

        # First request should succeed
        response1 = await middleware.dispatch(request, call_next)
        assert response1.status_code == 200  # noqa: PLR2004

        # Second request should be rate limited
        response2 = await middleware.dispatch(request, call_next)

        assert response2.status_code == 429  # noqa: PLR2004

    async def test_headers_added_to_response(
        self,
        middleware: RateLimitMiddleware,
    ) -> None:
        """Rate limit headers should be added to responses."""
        request = self._create_request()
        response = Response()
        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(request, call_next)

        assert "X-RateLimit-Limit" in result.headers
        assert "X-RateLimit-Remaining" in result.headers

    def test_get_client_ip_from_forwarded(
        self,
        middleware: RateLimitMiddleware,
    ) -> None:
        """Should extract IP from X-Forwarded-For header."""
        request = self._create_request(headers={"X-Forwarded-For": "1.2.3.4, 5.6.7.8"})

        ip = middleware._get_client_ip(request)  # noqa: SLF001

        assert ip == "1.2.3.4"

    def test_get_client_ip_from_real_ip(
        self,
        middleware: RateLimitMiddleware,
    ) -> None:
        """Should extract IP from X-Real-IP header."""
        request = self._create_request(headers={"X-Real-IP": "10.0.0.1"})

        ip = middleware._get_client_ip(request)  # noqa: SLF001

        assert ip == "10.0.0.1"

    def test_get_client_ip_fallback_to_client(
        self,
        middleware: RateLimitMiddleware,
    ) -> None:
        """Should fallback to request.client.host."""
        request = self._create_request(client_host="192.168.1.1")

        ip = middleware._get_client_ip(request)  # noqa: SLF001

        assert ip == "192.168.1.1"

    def test_get_client_ip_unknown(
        self,
        middleware: RateLimitMiddleware,
    ) -> None:
        """Should return 'unknown' when no IP available."""
        scope: RequestScope = {
            "type": "http",
            "path": "/test",
            "headers": [],
            "client": None,
        }
        request = Request(cast(dict[str, Any], scope))

        ip = middleware._get_client_ip(request)  # noqa: SLF001

        assert ip == "unknown"

    def test_get_client_ip_forwarded_with_spaces(
        self,
        middleware: RateLimitMiddleware,
    ) -> None:
        """Should trim spaces from forwarded IP."""
        request = self._create_request(headers={"X-Forwarded-For": "  1.2.3.4  , 5.6.7.8"})

        ip = middleware._get_client_ip(request)  # noqa: SLF001

        assert ip == "1.2.3.4"
