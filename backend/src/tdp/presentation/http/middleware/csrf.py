"""CSRF protection middleware — Double Submit Cookie pattern.

Flow:
  1. Client GET /api/csrf-token → token in response body + cookie
  2. Client sends X-CSrf-Token header on POST/PUT/PATCH/DELETE
  3. Middleware validates header value == cookie value

Uses timing-safe comparison to prevent timing attacks.
"""

from __future__ import annotations

import secrets

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

_WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_SAFE_PATHS = frozenset({
    "/api/csrf-token",
    "/api/health",
    "/api/docs",
    "/api/openapi.json",
})

CSRF_COOKIE_NAME = "csrftoken"
CSRF_HEADER_NAME = "x-csrf-token"


class CsrfProtectionMiddleware(BaseHTTPMiddleware):
    """Validates CSRF tokens on mutating requests."""

    def __init__(
        self,
        app,
        *,
        enabled: bool = True,
        cookie_secure: bool = False,
        cookie_samesite: str = "lax",
    ) -> None:
        super().__init__(app)
        self._enabled = enabled
        self._cookie_secure = cookie_secure
        self._cookie_samesite = cookie_samesite

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # ── Issue CSRF token (always active, regardless of enabled flag) ──
        if request.method == "GET" and request.url.path == "/api/csrf-token":
            token = secrets.token_hex(32)
            response = JSONResponse({"success": True, "data": {"csrf_token": token}})
            response.set_cookie(
                key=CSRF_COOKIE_NAME,
                value=token,
                httponly=False,
                secure=self._cookie_secure,
                samesite=self._cookie_samesite,
                max_age=86400,
                path="/",
            )
            return response

        # ── Skip validation when disabled ──
        if not self._enabled:
            return await call_next(request)

        # ── Skip safe methods ──
        if request.method not in _WRITE_METHODS:
            return await call_next(request)

        # ── Skip safe paths ──
        if request.url.path in _SAFE_PATHS:
            return await call_next(request)
        if any(request.url.path.startswith(p) for p in ("/api/docs", "/api/openapi")):
            return await call_next(request)

        # ── Validate CSRF token ──
        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        header_token = request.headers.get(CSRF_HEADER_NAME)

        if not cookie_token or not header_token:
            return JSONResponse(
                {
                    "success": False,
                    "message": "CSRF token missing",
                    "code": "CSRF_TOKEN_MISSING",
                },
                status_code=403,
            )

        if not secrets.compare_digest(cookie_token, header_token):
            return JSONResponse(
                {
                    "success": False,
                    "message": "CSRF token mismatch",
                    "code": "CSRF_TOKEN_MISMATCH",
                },
                status_code=403,
            )

        return await call_next(request)