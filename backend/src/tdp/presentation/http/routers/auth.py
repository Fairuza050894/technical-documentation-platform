"""Auth endpoints.

Endpoints:
  GET  /api/auth/session  — current session info
  POST /api/auth/refresh  — refresh access token
  POST /api/auth/logout   — revoke current token
"""

from __future__ import annotations

from datetime import datetime, timezone

import jwt as pyjwt
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from tdp.identity.jwt_service import JwtService, JwtValidationError
from tdp.identity.session_store import TokenBlacklist
from tdp.presentation.http.dependencies.identity import PrincipalDependency

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Response models ──


class SessionResponse(BaseModel):
    subject_id: str
    display_name: str
    email: str
    provider: str
    assurance: str


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LogoutResponse(BaseModel):
    success: bool
    message: str


# ── Endpoints ──


@router.get("/session", response_model=SessionResponse)
async def get_session(principal: PrincipalDependency) -> SessionResponse:
    """Return current session information from the validated token."""
    return SessionResponse(
        subject_id=principal.subject_id,
        display_name=principal.display_name,
        email=principal.email,
        provider=principal.provider,
        assurance=principal.assurance.value,
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    request: Request,
    body: RefreshRequest,
) -> RefreshResponse:
    """Exchange a refresh token for a new access token."""
    jwt_service: JwtService = request.app.state.jwt_service
    try:
        result = await jwt_service.refresh_token(body.refresh_token)
        return RefreshResponse(
            access_token=result["access_token"],
            expires_in=result.get("expires_in", 3600),
        )
    except JwtValidationError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    principal: PrincipalDependency,
) -> LogoutResponse:
    """Revoke the current access token (add to blacklist)."""
    auth_header = request.headers.get("Authorization", "")

    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            # Decode without verification — we just need jti and exp
            claims = pyjwt.decode(token, options={"verify_signature": False})
            jti = claims.get("jti")
            exp = claims.get("exp")

            if jti and exp:
                blacklist: TokenBlacklist = request.app.state.token_blacklist
                expires_at = datetime.fromtimestamp(exp, tz=timezone.utc).isoformat()
                blacklist.add(jti, expires_at)
        except Exception:
            pass  # Best-effort — logout still succeeds

    return LogoutResponse(success=True, message="Logged out successfully")