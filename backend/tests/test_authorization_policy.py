"""Tests for authorization policy."""
from __future__ import annotations

from tdp.authorization.model import Permission, Role
from tdp.authorization.policy import AuthorizationPolicy, SeparationOfDutiesPolicy


class _MockLookup:
    def __init__(self, roles: dict[tuple[str, str], frozenset[Role]]) -> None:
        self._roles = roles

    def get_roles(self, subject_id: str, workspace_id: str) -> frozenset[Role]:
        return self._roles.get((subject_id, workspace_id), frozenset())


class TestAuthorizationPolicy:
    def test_admin_subject_bypasses(self) -> None:
        p = AuthorizationPolicy(_MockLookup({}), default_admin_subjects=("admin",))
        assert p.has_permission("admin", "ws-1", Permission.DOCUMENT_WRITE)
        assert p.has_permission("admin", "ws-1", Permission.WORKSPACE_ADMIN)

    def test_member_has_role_permissions(self) -> None:
        p = AuthorizationPolicy(_MockLookup({
            ("u1", "ws-1"): frozenset({Role.DOCUMENT_AUTHOR}),
        }))
        assert p.has_permission("u1", "ws-1", Permission.DOCUMENT_WRITE)
        assert p.has_permission("u1", "ws-1", Permission.DOCUMENT_READ)

    def test_member_lacks_ungranted(self) -> None:
        p = AuthorizationPolicy(_MockLookup({
            ("u1", "ws-1"): frozenset({Role.DOCUMENT_AUTHOR}),
        }))
        assert not p.has_permission("u1", "ws-1", Permission.DOCUMENT_APPROVE)
        assert not p.has_permission("u1", "ws-1", Permission.WORKSPACE_ADMIN)

    def test_non_member_denied(self) -> None:
        p = AuthorizationPolicy(_MockLookup({}))
        assert not p.has_permission("u1", "ws-1", Permission.DOCUMENT_READ)

    def test_viewer_read_only(self) -> None:
        p = AuthorizationPolicy(_MockLookup({
            ("u1", "ws-1"): frozenset({Role.VIEWER}),
        }))
        assert p.has_permission("u1", "ws-1", Permission.DOCUMENT_READ)
        assert not p.has_permission("u1", "ws-1", Permission.DOCUMENT_WRITE)

    def test_effective_permissions_admin(self) -> None:
        p = AuthorizationPolicy(_MockLookup({}), default_admin_subjects=("admin",))
        assert p.get_effective_permissions("admin", "ws-1") == frozenset(Permission)

    def test_effective_permissions_member(self) -> None:
        p = AuthorizationPolicy(_MockLookup({
            ("u1", "ws-1"): frozenset({Role.REVIEWER}),
        }))
        perms = p.get_effective_permissions("u1", "ws-1")
        assert Permission.DOCUMENT_REVIEW in perms
        assert Permission.DOCUMENT_APPROVE not in perms


class TestSeparationOfDutiesPolicy:
    def test_author_cannot_approve(self) -> None:
        assert not SeparationOfDutiesPolicy.can_act_on_document(
            "u1", "u1", Permission.DOCUMENT_APPROVE,
        )

    def test_author_cannot_review(self) -> None:
        assert not SeparationOfDutiesPolicy.can_act_on_document(
            "u1", "u1", Permission.DOCUMENT_REVIEW,
        )

    def test_other_can_approve(self) -> None:
        assert SeparationOfDutiesPolicy.can_act_on_document(
            "u2", "u1", Permission.DOCUMENT_APPROVE,
        )

    def test_author_can_read(self) -> None:
        assert SeparationOfDutiesPolicy.can_act_on_document(
            "u1", "u1", Permission.DOCUMENT_READ,
        )

    def test_author_can_write(self) -> None:
        assert SeparationOfDutiesPolicy.can_act_on_document(
            "u1", "u1", Permission.DOCUMENT_WRITE,
        )
