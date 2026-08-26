"""FastAPI dependencies for authorization enforcement.

Usage::

    from tdp.authorization.guards import require_workspace_permission
    from tdp.authorization.model import Permission

    @router.post("/documents/{workspace_id}")
    async def create(
        _auth: None = require_workspace_permission(Permission.DOCUMENT_WRITE),
    ) -> ...:
        ...
"""
from __future__ import annotations

from fastapi import Depends, Request

from tdp.authorization.errors import PermissionDeniedError
from tdp.authorization.model import Permission
from tdp.authorization.policy import AuthorizationPolicy


def require_workspace_permission(
    permission: Permission,
    workspace_id_param: str = "workspace_id",
) -> Depends:
    """Return a FastAPI dependency that enforces a workspace-level permission."""

    async def _guard(request: Request) -> None:
        policy: AuthorizationPolicy = request.app.state.authorization_policy
        principal = getattr(request.state, "principal", None)
        principal_id = (
            getattr(principal, "subject_id", "anonymous") if principal else "anonymous"
        )
        workspace_id: str = request.path_params.get(workspace_id_param, "")

        if not policy.has_permission(principal_id, workspace_id, permission):
            raise PermissionDeniedError(
                principal_id=principal_id,
                permission=permission.value,
                workspace_id=workspace_id,
            )

    return Depends(_guard)
