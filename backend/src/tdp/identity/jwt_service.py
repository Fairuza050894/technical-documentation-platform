"""JWT validation service.

Validates JWT tokens and extracts claims into RequestPrincipal.
"""

from __future__ import annotations

from typing import Any

import httpx
import jwt
from jwt.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidTokenError,
)

from tdp.identity.model import IdentityAssurance, RequestPrincipal
from tdp.identity.oidc import OidcDiscovery


class JwtValidationError(Exception):
    """Raised when JWT validation fails."""

    def __init__(self, message: str, code: str = "INVALID_TOKEN") -> None:
        super().__init__(message)
        self.code = code


class JwtService:
    """Validates JWT tokens and extracts claims."""

    def __init__(
        self,
        oidc_discovery: OidcDiscovery,
        audience: str | None = None,
    ) -> None:
        self._discovery = oidc_discovery
        self._audience = audience or oidc_discovery.client_id

    async def validate_token(self, token: str) -> dict[str, Any]:
        """Validate a JWT token and return its claims."""
        try:
            signing_key = await self._discovery.get_signing_key(token)

            claims = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"],
                audience=self._audience,
                issuer=self._discovery.issuer,
                options={
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True,
                },
            )

            return claims

        except ExpiredSignatureError:
            raise JwtValidationError("Token has expired", "TOKEN_EXPIRED")
        except InvalidAudienceError:
            raise JwtValidationError("Invalid token audience", "INVALID_AUDIENCE")
        except InvalidIssuerError:
            raise JwtValidationError("Invalid token issuer", "INVALID_ISSUER")
        except DecodeError:
            raise JwtValidationError("Invalid token format", "INVALID_FORMAT")
        except InvalidTokenError as e:
            raise JwtValidationError(f"Invalid token: {e}", "INVALID_TOKEN")

    async def extract_principal(self, token: str) -> RequestPrincipal:
        """Extract a RequestPrincipal from a validated JWT token."""
        claims = await self.validate_token(token)

        subject_id = claims.get("sub", "")
        display_name = claims.get(
            "name", claims.get("preferred_username", subject_id)
        )
        email = claims.get("email", "")

        return RequestPrincipal(
            subject_id=subject_id,
            display_name=display_name,
            email=email,
            provider="oidc",
            assurance=IdentityAssurance.VERIFIED,
        )

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh an access token using a refresh token."""
        token_endpoint = await self._discovery.get_token_endpoint()

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                token_endpoint,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self._discovery.client_id,
                    "client_secret": self._discovery.client_secret,
                },
            )

            if response.status_code != 200:
                raise JwtValidationError("Token refresh failed", "REFRESH_FAILED")

            return response.json()