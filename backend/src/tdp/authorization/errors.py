"""Authorization domain errors."""
from __future__ import annotations

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


async def permission_denied_handler(
    request: Request, exc: PermissionDeniedError
) -> JSONResponse:
    """FastAPI exception handler for PermissionDeniedError."""
    return JSONResponse(
        status_code=403,
        content={
            "error": "permission_denied",
            "message": exc.message,
            "principal_id": exc.principal_id,
            "permission": exc.permission,
            "workspace_id": exc.workspace_id,
        },
    )
