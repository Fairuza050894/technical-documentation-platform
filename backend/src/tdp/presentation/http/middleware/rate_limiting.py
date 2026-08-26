"""In-memory sliding-window rate limiter.

Suitable for single-process deployments.  For multi-worker or
multi-node setups, replace the in-memory dict with Redis.

Reference: OWASP ASVS 4.0 — V11.1 Business Logic Security
"""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class SlidingWindowRateLimiter:
    """Thread-safe sliding window counter keyed by client IP."""

    def __init__(self, requests_per_minute: int) -> None:
        self._window_seconds: int = 60
        self._max_requests: int = requests_per_minute
        self._windows: dict[str, list[float]] = defaultdict(list)
        self._lock: Lock = Lock()

    @property
    def max_requests(self) -> int:
        return self._max_requests

    def is_allowed(self, key: str) -> tuple[bool, int, int]:
        """Return (allowed, remaining, reset_epoch)."""
        now = time.time()
        window_start = now - self._window_seconds

        with self._lock:
            timestamps = self._windows[key]
            self._windows[key] = [t for t in timestamps if t > window_start]

            current = len(self._windows[key])
            if current >= self._max_requests:
                oldest = self._windows[key][0]
                reset_epoch = int(oldest + self._window_seconds)
                return False, 0, reset_epoch

            self._windows[key].append(now)
            remaining = self._max_requests - current - 1
            reset_epoch = int(now + self._window_seconds)
            return True, remaining, reset_epoch


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rejects requests that exceed the per-IP rate limit."""

    def __init__(self, app, requests_per_minute: int = 60) -> None:
        super().__init__(app)
        self._limiter = SlidingWindowRateLimiter(requests_per_minute)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        allowed, remaining, reset_epoch = self._limiter.is_allowed(client_ip)

        if not allowed:
            retry_after = max(reset_epoch - int(time.time()), 1)
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": retry_after,
                },
                headers={
                    "X-RateLimit-Limit": str(self._limiter.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_epoch),
                    "Retry-After": str(retry_after),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self._limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_epoch)
        return response
