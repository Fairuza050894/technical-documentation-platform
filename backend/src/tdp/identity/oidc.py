"""OIDC discovery and JWKS caching.

Fetches the OpenID Connect discovery document and caches
JWKS (JSON Web Key Set) for token validation.
"""

from __future__ import annotations

import time
from typing import Any

import httpx
import jwt
from jwt.algorithms import RSAAlgorithm


class OidcDiscovery:
    """OIDC discovery document and JWKS cache."""

    def __init__(self, issuer: str, client_id: str, client_secret: str = "") -> None:
        self._issuer = issuer.rstrip("/")
        self._client_id = client_id
        self._client_secret = client_secret
        self._config: dict[str, Any] | None = None
        self._jwks: dict[str, Any] | None = None
        self._jwks_expires_at: float = 0
        self._jwks_ttl: float = 3600  # 1 hour

    @property
    def issuer(self) -> str:
        return self._issuer

    @property
    def client_id(self) -> str:
        return self._client_id

    @property
    def client_secret(self) -> str:
        return self._client_secret

    async def discover(self) -> dict[str, Any]:
        """Fetch and cache the OIDC discovery document."""
        if self._config is not None:
            return self._config

        url = f"{self._issuer}/.well-known/openid-configuration"
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
            self._config = response.json()

        return self._config

    async def get_jwks(self) -> dict[str, Any]:
        """Fetch and cache JWKS keys."""
        now = time.time()
        if self._jwks is not None and now < self._jwks_expires_at:
            return self._jwks

        config = await self.discover()
        jwks_uri = config["jwks_uri"]

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(jwks_uri)
            response.raise_for_status()
            self._jwks = response.json()

        self._jwks_expires_at = now + self._jwks_ttl
        return self._jwks

    async def get_signing_key(self, token: str) -> Any:
        """Get the signing key for a JWT token."""
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        jwks = await self.get_jwks()

        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return RSAAlgorithm.from_jwk(key)

        # Key not found — refresh JWKS and retry (key rotation)
        self._jwks = None
        jwks = await self.get_jwks()
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return RSAAlgorithm.from_jwk(key)

        raise ValueError(f"Unable to find signing key for kid: {kid}")

    async def get_token_endpoint(self) -> str:
        """Get the token endpoint URL."""
        config = await self.discover()
        return config["token_endpoint"]

    async def get_end_session_endpoint(self) -> str | None:
        """Get the end session endpoint URL (if available)."""
        config = await self.discover()
        return config.get("end_session_endpoint")

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._config = None
        self._jwks = None
        self._jwks_expires_at = 0