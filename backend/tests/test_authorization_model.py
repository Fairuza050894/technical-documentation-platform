"""Tests for authorization model."""
from __future__ import annotations

from tdp.authorization.model import ROLE_PERMISSIONS, Permission, Role


class TestRole:
    def test_enum_values(self) -> None:
        assert Role.ADMIN == "admin"
        assert Role.DOCUMENT_AUTHOR == "document_author"
        assert Role.REVIEWER == "reviewer"
        assert Role.APPROVER == "approver"
        assert Role.VIEWER == "viewer"

    def test_five_roles(self) -> None:
        assert len(Role) == 5


class TestPermission:
    def test_enum_values(self) -> None:
        assert Permission.DOCUMENT_READ == "document:read"
        assert Permission.WORKSPACE_ADMIN == "workspace:admin"

    def test_nineteen_permissions(self) -> None:
        assert len(Permission) == 19


class TestRolePermissions:
    def test_admin_has_all_permissions(self) -> None:
        for perm in Permission:
            assert perm in ROLE_PERMISSIONS[Role.ADMIN]

    def test_viewer_has_only_read(self) -> None:
        for perm in ROLE_PERMISSIONS[Role.VIEWER]:
            assert ":read" in perm.value

    def test_all_roles_in_mapping(self) -> None:
        for role in Role:
            assert role in ROLE_PERMISSIONS

    def test_author_cannot_approve(self) -> None:
        assert Permission.DOCUMENT_APPROVE not in ROLE_PERMISSIONS[Role.DOCUMENT_AUTHOR]

    def test_author_cannot_review(self) -> None:
        assert Permission.DOCUMENT_REVIEW not in ROLE_PERMISSIONS[Role.DOCUMENT_AUTHOR]

    def test_reviewer_can_review(self) -> None:
        assert Permission.DOCUMENT_REVIEW in ROLE_PERMISSIONS[Role.REVIEWER]

    def test_approver_can_approve(self) -> None:
        assert Permission.DOCUMENT_APPROVE in ROLE_PERMISSIONS[Role.APPROVER]
