"""Authorization policy engine.

Evaluates whether a principal has a specific permission in a workspace
by combining workspace membership roles with the role-permission mapping.
"""
from __future__ import annotations

from typing import Protocol

from tdp.authorization.model import Permission, Role, ROLE_PERMISSIONS


class MembershipLookup(Protocol):
    """Port for retrieving a user's roles within a workspace."""

    def get_roles(self, subject_id: str, workspace_id: str) -> frozenset[Role]: ...


class AuthorizationPolicy:
    """Determines whether a principal has a specific permission in a workspace.

    Default admin subjects bypass membership checks and receive all permissions.
    """

    def __init__(
        self,
        membership_lookup: MembershipLookup,
        default_admin_subjects: tuple[str, ...] = (),
    ) -> None:
        self._membership = membership_lookup
        self._admin_subjects = frozenset(default_admin_subjects)

    def has_permission(
        self,
        subject_id: str,
        workspace_id: str,
        permission: Permission,
    ) -> bool:
        """Check if subject_id has permission in workspace_id."""
        if subject_id in self._admin_subjects:
            return True
        roles = self._membership.get_roles(subject_id, workspace_id)
        return any(
            permission in ROLE_PERMISSIONS.get(role, frozenset()) for role in roles
        )

    def get_effective_permissions(
        self,
        subject_id: str,
        workspace_id: str,
    ) -> frozenset[Permission]:
        """Return the union of all permissions granted by the subject's roles."""
        if subject_id in self._admin_subjects:
            return frozenset(Permission)
        roles = self._membership.get_roles(subject_id, workspace_id)
        permissions: set[Permission] = set()
        for role in roles:
            permissions |= ROLE_PERMISSIONS.get(role, frozenset())
        return frozenset(permissions)


class SeparationOfDutiesPolicy:
    """Enforces that the same person cannot both author and approve/review.

    Reference: ISO/IEC 27001:2022 A.5.3 (Segregation of duties)
    """

    _RESTRICTED: frozenset[Permission] = frozenset({
        Permission.DOCUMENT_APPROVE,
        Permission.DOCUMENT_REVIEW,
    })

    @staticmethod
    def can_act_on_document(
        actor_id: str,
        document_author_id: str,
        requested_permission: Permission,
    ) -> bool:
        """Return True if actor is allowed to perform the action."""
        if requested_permission in SeparationOfDutiesPolicy._RESTRICTED:
            return actor_id != document_author_id
        return True
