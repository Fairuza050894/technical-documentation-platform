"""Tests for audit trail module."""
from __future__ import annotations

import pytest

from tdp.audit.model import AuditAction, AuditEvent


class TestAuditAction:
    def test_action_values(self) -> None:
        assert AuditAction.CREATE == "create"
        assert AuditAction.APPROVE == "approve"
        assert AuditAction.LOGIN == "login"

    def test_action_is_str(self) -> None:
        assert isinstance(AuditAction.CREATE, str)


class TestAuditEvent:
    def test_defaults(self) -> None:
        event = AuditEvent()
        assert event.actor_id == ""
        assert event.action == AuditAction.READ
        assert event.success is True
        assert event.event_id

    def test_custom_values(self) -> None:
        event = AuditEvent(
            actor_id="user-1",
            action=AuditAction.CREATE,
            resource_type="document",
            resource_id="doc-123",
            workspace_id="ws-1",
        )
        assert event.actor_id == "user-1"
        assert event.action == AuditAction.CREATE
        assert event.resource_id == "doc-123"
        assert event.workspace_id == "ws-1"

    def test_frozen(self) -> None:
        event = AuditEvent()
        with pytest.raises(AttributeError):
            event.actor_id = "changed"  # type: ignore[misc]

    def test_unique_ids(self) -> None:
        a = AuditEvent()
        b = AuditEvent()
        assert a.event_id != b.event_id

    def test_metadata_default_empty(self) -> None:
        event = AuditEvent()
        assert event.metadata == {}
