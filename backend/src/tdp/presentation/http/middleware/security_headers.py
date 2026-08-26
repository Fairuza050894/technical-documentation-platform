"""Security headers middleware.

Provides:
- Strict-Transport-Security (HSTS) — production only
- Content-Security-Policy (CSP) — strict nonce-based policy
- X-Content-Type-Options, X-Frame-Options, Referrer-Policy
- Permissions-Policy, Cross-Origin isolation headers
"""

from __future__ import annotations

import secrets

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SecurityHeadersMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        environment: str = "development",
        hsts_max_age: int = 31_536_000,
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False,
    ) -> None:
        self._app = app
        self._environment = environment
        self._hsts_max_age = hsts_max_age
        self._hsts_include_subdomains = hsts_include_subdomains
        self._hsts_preload = hsts_preload

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        # Generate nonce per-request for CSP
        nonce = secrets.token_urlsafe(16)
        scope["csp_nonce"] = nonce

        path = scope.get("path", "")

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)

                # ── HSTS (production only) ──
                if self._environment == "production":
                    hsts = f"max-age={self._hsts_max_age}"
                    if self._hsts_include_subdomains:
                        hsts += "; includeSubDomains"
                    if self._hsts_preload:
                        hsts += "; preload"
                    headers["Strict-Transport-Security"] = hsts

                # ── CSP — path-aware ──
                if path.startswith("/api/docs") or path.startswith("/api/redoc"):
                    # Swagger UI / ReDoc need relaxed CSP
                    headers["Content-Security-Policy"] = (
                        "default-src 'self'; "
                        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                        "style-src 'self' 'unsafe-inline'; "
                        "img-src 'self' data: https:; "
                        "font-src 'self'; "
                        "frame-ancestors 'none'; "
                        "base-uri 'self'"
                    )
                else:
                    # Strict CSP for all API endpoints
                    headers["Content-Security-Policy"] = (
                        f"default-src 'none'; "
                        f"script-src 'nonce-{nonce}'; "
                        f"style-src 'nonce-{nonce}'; "
                        f"img-src 'none'; "
                        f"font-src 'none'; "
                        f"connect-src 'self'; "
                        f"frame-ancestors 'none'; "
                        f"base-uri 'none'; "
                        f"form-action 'none'; "
                        f"object-src 'none'; "
                        f"upgrade-insecure-requests; "
                        f"block-all-mixed-content"
                    )

                # ── Standard security headers ──
                headers["X-Content-Type-Options"] = "nosniff"
                headers["X-Frame-Options"] = "DENY"
                headers["Referrer-Policy"] = "no-referrer"
                headers["Permissions-Policy"] = (
                    "camera=(), microphone=(), geolocation=()"
                )

                # ── Cross-Origin isolation ──
                headers["Cross-Origin-Opener-Policy"] = "same-origin"
                headers["Cross-Origin-Resource-Policy"] = "same-origin"
                headers["Cross-Origin-Embedder-Policy"] = "require-corp"

            await send(message)

        await self._app(scope, receive, send_with_headers)