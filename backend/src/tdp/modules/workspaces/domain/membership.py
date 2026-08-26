"""Workspace membership domain model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol

from tdp.authorization.model import Role


@dataclass(frozen=True)
class WorkspaceMember:
    """A user's membership in a workspace with a specific role."""

    workspace_id: str
    subject_id: str
    role: Role
    added_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    added_by: str = ""


class MembershipRepository(Protocol):
    """Port for persisting workspace membership."""

    def add_member(self, member: WorkspaceMember) -> None: ...

    def remove_member(
        self, workspace_id: str, subject_id: str, role: Role
    ) -> None: ...

    def get_roles(self, subject_id: str, workspace_id: str) -> frozenset[Role]: ...

    def list_members(self, workspace_id: str) -> list[WorkspaceMember]: ...

    def list_workspaces_for_subject(self, subject_id: str) -> list[str]: ...
