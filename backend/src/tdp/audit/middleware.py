"""ASGI audit middleware for FastAPI.

Intercepts every write request (POST/PUT/PATCH/DELETE) and
produces an AuditEvent *after* the response has been generated
so that the status code is captured.
"""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from tdp.audit.logger import StructuredAuditLogger
from tdp.audit.model import AuditAction, AuditEvent

_WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

_METHOD_ACTION_MAP: dict[str, AuditAction] = {
    "POST": AuditAction.CREATE,
    "PUT": AuditAction.UPDATE,
    "PATCH": AuditAction.UPDATE,
    "DELETE": AuditAction.DELETE,
}


class AuditMiddleware(BaseHTTPMiddleware):
    """Records an audit event for every state-changing request."""

    def __init__(self, app, audit_logger: StructuredAuditLogger) -> None:
        super().__init__(app)
        self._audit = audit_logger

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _WRITE_METHODS:
            return await call_next(request)

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 2)

        principal = getattr(request.state, "principal", None)

        event = AuditEvent(
            actor_id=getattr(principal, "subject_id", "anonymous") if principal else "anonymous",
            actor_display_name=(getattr(principal, "display_name", "") if principal else ""),
            action=_METHOD_ACTION_MAP.get(request.method, AuditAction.UPDATE),
            resource_type=request.url.path,
            request_id=getattr(request.state, "request_id", ""),
            ip_address=request.client.host if request.client else "",
            success=200 <= response.status_code < 400,
            metadata={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        self._audit.record(event)
        return response
