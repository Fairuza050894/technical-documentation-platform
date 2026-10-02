"""Authorization domain errors."""

from __future__ import annotations

from typing import cast

from starlette.requests import Request
from starlette.responses import JSONResponse


class AuthorizationError(Exception):
    """Base authorization error."""

    def __init__(
        self,
        message: str,
        principal_id: str = "",
        permission: str = "",
        workspace_id: str = "",
    ) -> None:
        self.message = message
        self.principal_id = principal_id
        self.permission = permission
        self.workspace_id = workspace_id
        super().__init__(message)


class PermissionDeniedError(AuthorizationError):
    """Raised when a principal lacks the required permission."""

    def __init__(
        self,
        principal_id: str,
        permission: str,
        workspace_id: str = "",
    ) -> None:
        detail = f"Permission denied: '{permission}'"
        if workspace_id:
            detail += f" in workspace {workspace_id}"
        super().__init__(
            message=detail,
            principal_id=principal_id,
            permission=permission,
            workspace_id=workspace_id,
        )


async def permission_denied_handler(request: Request, exc: Exception) -> JSONResponse:
    """FastAPI exception handler for PermissionDeniedError."""
    permission_error = cast(PermissionDeniedError, exc)
    return JSONResponse(
        status_code=403,
        content={
            "error": "permission_denied",
            "message": permission_error.message,
            "principal_id": permission_error.principal_id,
            "permission": permission_error.permission,
            "workspace_id": permission_error.workspace_id,
        },
    )
