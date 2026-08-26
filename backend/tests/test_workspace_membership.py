"""Tests for workspace membership."""
from __future__ import annotations

from pathlib import Path

import pytest

from tdp.authorization.model import Role
from tdp.modules.workspaces.domain.membership import WorkspaceMember
from tdp.modules.workspaces.infrastructure.membership_repository import (
    SqliteMembershipRepository,
)


class TestWorkspaceMember:
    def test_creation(self) -> None:
        m = WorkspaceMember(workspace_id="ws-1", subject_id="u1", role=Role.VIEWER, added_by="admin")
        assert m.workspace_id == "ws-1"
        assert m.role == Role.VIEWER

    def test_frozen(self) -> None:
        m = WorkspaceMember(workspace_id="ws-1", subject_id="u1", role=Role.VIEWER, added_by="admin")
        with pytest.raises(AttributeError):
            m.role = Role.ADMIN  # type: ignore[misc]


class TestSqliteMembershipRepository:
    def test_add_and_get(self, tmp_path: Path) -> None:
        repo = SqliteMembershipRepository(tmp_path / "t.db")
        repo.add_member(WorkspaceMember("ws-1", "u1", Role.DOCUMENT_AUTHOR, added_by="admin"))
        assert Role.DOCUMENT_AUTHOR in repo.get_roles("u1", "ws-1")

    def test_multiple_roles(self, tmp_path: Path) -> None:
        repo = SqliteMembershipRepository(tmp_path / "t.db")
        repo.add_member(WorkspaceMember("ws-1", "u1", Role.DOCUMENT_AUTHOR, added_by="admin"))
        repo.add_member(WorkspaceMember("ws-1", "u1", Role.REVIEWER, added_by="admin"))
        roles = repo.get_roles("u1", "ws-1")
        assert Role.DOCUMENT_AUTHOR in roles
        assert Role.REVIEWER in roles

    def test_remove(self, tmp_path: Path) -> None:
        repo = SqliteMembershipRepository(tmp_path / "t.db")
        repo.add_member(WorkspaceMember("ws-1", "u1", Role.DOCUMENT_AUTHOR, added_by="admin"))
        repo.remove_member("ws-1", "u1", Role.DOCUMENT_AUTHOR)
        assert len(repo.get_roles("u1", "ws-1")) == 0

    def test_list_members(self, tmp_path: Path) -> None:
        repo = SqliteMembershipRepository(tmp_path / "t.db")
        repo.add_member(WorkspaceMember("ws-1", "u1", Role.VIEWER, added_by="admin"))
        repo.add_member(WorkspaceMember("ws-1", "u2", Role.VIEWER, added_by="admin"))
        assert len(repo.list_members("ws-1")) == 2

    def test_list_workspaces(self, tmp_path: Path) -> None:
        repo = SqliteMembershipRepository(tmp_path / "t.db")
        repo.add_member(WorkspaceMember("ws-1", "u1", Role.VIEWER, added_by="admin"))
        repo.add_member(WorkspaceMember("ws-2", "u1", Role.VIEWER, added_by="admin"))
        ws = repo.list_workspaces_for_subject("u1")
        assert "ws-1" in ws and "ws-2" in ws

    def test_empty_get_roles(self, tmp_path: Path) -> None:
        repo = SqliteMembershipRepository(tmp_path / "t.db")
        assert len(repo.get_roles("nobody", "ws-1")) == 0

    def test_workspace_isolation(self, tmp_path: Path) -> None:
        repo = SqliteMembershipRepository(tmp_path / "t.db")
        repo.add_member(WorkspaceMember("ws-1", "u1", Role.ADMIN, added_by="admin"))
        assert len(repo.get_roles("u1", "ws-2")) == 0
