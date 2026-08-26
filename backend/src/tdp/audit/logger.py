"""Structured audit logger.

Writes audit events as structured log entries via structlog
AND persists them to SQLite for queryable audit trail.
"""

from __future__ import annotations

import structlog

from tdp.audit.model import AuditEvent
from tdp.audit.store import AuditStore

logger = structlog.stdlib.get_logger("audit")


class StructuredAuditLogger:
    """Thin facade that serialises AuditEvent into structlog and SQLite."""

    def __init__(self, enabled: bool = True, store: AuditStore | None = None) -> None:
        self._enabled = enabled
        self._store = store

    @property
    def enabled(self) -> bool:
        return self._enabled

    def record(self, event: AuditEvent) -> None:
        """Persist a single audit event to structlog and SQLite."""
        if not self._enabled:
            return

        # ── Structlog (existing — stdout/SIEM) ──
        logger.info(
            "audit_event",
            event_id=event.event_id,
            timestamp=event.timestamp.isoformat(),
            actor_id=event.actor_id,
            actor_display_name=event.actor_display_name,
            action=event.action.value,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            workspace_id=event.workspace_id,
            project_id=event.project_id,
            request_id=event.request_id,
            ip_address=event.ip_address,
            success=event.success,
            error_message=event.error_message,
            **event.metadata,
        )

        # ── SQLite (new — queryable audit trail) ──
        if self._store:
            try:
                self._store.insert(event)
            except Exception:
                logger.warning("audit_store_write_failed", event_id=event.event_id)