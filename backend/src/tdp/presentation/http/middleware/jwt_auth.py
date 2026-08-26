"""JWT authentication middleware.

Extracts Bearer token from Authorization header,
validates it, and sets request.state.principal.
"""

from __future__ import annotations

import jwt as pyjwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from tdp.identity.jwt_service import JwtService, JwtValidationError
from tdp.identity.session_store import TokenBlacklist

_PUBLIC_PATHS = frozenset({
    "/api/health",
    "/api/docs",
    "/api/openapi.json",
    "/api/csrf-token",
    "/api/auth/refresh",
})


class JwtAuthMiddleware(BaseHTTPMiddleware):
    """Validates JWT tokens on protected endpoints."""

    def __init__(
        self,
        app,
        jwt_service: JwtService,
        token_blacklist: TokenBlacklist,
        auth_mode: str = "oidc",
    ) -> None:
        super().__init__(app)
        self._jwt_service = jwt_service
        self._token_blacklist = token_blacklist
        self._auth_mode = auth_mode

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip if not in OIDC mode
        if self._auth_mode != "oidc":
            return await call_next(request)

        # Skip public paths
        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)
        if any(request.url.path.startswith(p) for p in ("/api/docs", "/api/openapi")):
            return await call_next(request)

        # Extract Bearer token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                {
                    "success": False,
                    "message": "Missing or invalid Authorization header",
                    "code": "MISSING_TOKEN",
                },
                status_code=401,
            )

        token = auth_header[7:]

        # Check blacklist first (fast path — no crypto)
        try:
            unverified = pyjwt.decode(token, options={"verify_signature": False})
            jti = unverified.get("jti")
            if jti and self._token_blacklist.is_blacklisted(jti):
                return JSONResponse(
                    {
                        "success": False,
                        "message": "Token has been revoked",
                        "code": "TOKEN_REVOKED",
                    },
                    status_code=401,
                )
        except Exception:
            pass  # Will be caught by full validation below

        # Full token validation
        try:
            principal = await self._jwt_service.extract_principal(token)
            request.state.principal = principal
        except JwtValidationError as e:
            return JSONResponse(
                {"success": False, "message": str(e), "code": e.code},
                status_code=401,
            )

        return await call_next(request)