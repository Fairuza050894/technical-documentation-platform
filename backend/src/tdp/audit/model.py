"""Audit event domain model.

Reference: ISO/IEC 27001:2022 A.8.15 (Logging)
Every mutation on the system produces an immutable AuditEvent
that can be queried for compliance and incident investigation.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class AuditAction(StrEnum):
    """Classifies the operation that was performed."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    REVIEW = "review"
    APPROVE = "approve"
    REJECT = "reject"
    PUBLISH = "publish"
    ARCHIVE = "archive"
    EXPORT = "export"
    IMPORT = "import"
    LOGIN = "login"
    LOGOUT = "logout"


@dataclass(frozen=True)
class AuditEvent:
    """Immutable record of a single auditable action.

    Frozen dataclass guarantees that once written the event cannot
    be mutated — critical for forensic integrity.
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    actor_id: str = ""
    actor_display_name: str = ""
    action: AuditAction = AuditAction.READ
    resource_type: str = ""
    resource_id: str = ""
    workspace_id: str = ""
    project_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    request_id: str = ""
    ip_address: str = ""
    success: bool = True
    error_message: str = ""
