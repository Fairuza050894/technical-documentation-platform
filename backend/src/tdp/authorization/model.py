"""Role-Based Access Control model.

Reference: ISO/IEC 27001:2022 A.5.15 (Access control)
Defines roles, permissions, and the role-permission mapping
that governs workspace-level authorization decisions.
"""
from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    """Workspace-level roles that can be assigned to members."""

    ADMIN = "admin"
    DOCUMENT_AUTHOR = "document_author"
    REVIEWER = "reviewer"
    APPROVER = "approver"
    VIEWER = "viewer"


class Permission(StrEnum):
    """Fine-grained permissions for resource-level access control."""

    WORKSPACE_READ = "workspace:read"
    WORKSPACE_WRITE = "workspace:write"
    WORKSPACE_ADMIN = "workspace:admin"
    PROJECT_READ = "project:read"
    PROJECT_WRITE = "project:write"
    PROJECT_ADMIN = "project:admin"
    DOCUMENT_READ = "document:read"
    DOCUMENT_WRITE = "document:write"
    DOCUMENT_REVIEW = "document:review"
    DOCUMENT_APPROVE = "document:approve"
    SOURCE_READ = "source:read"
    SOURCE_WRITE = "source:write"
    EVIDENCE_READ = "evidence:read"
    EVIDENCE_WRITE = "evidence:write"
    FEATURE_READ = "feature:read"
    FEATURE_WRITE = "feature:write"
    CATALOG_READ = "catalog:read"
    MEMBER_READ = "member:read"
    MEMBER_WRITE = "member:write"


_READ: frozenset[Permission] = frozenset({
    Permission.WORKSPACE_READ,
    Permission.PROJECT_READ,
    Permission.DOCUMENT_READ,
    Permission.SOURCE_READ,
    Permission.EVIDENCE_READ,
    Permission.FEATURE_READ,
    Permission.CATALOG_READ,
    Permission.MEMBER_READ,
})

_WRITE: frozenset[Permission] = frozenset({
    Permission.WORKSPACE_WRITE,
    Permission.PROJECT_WRITE,
    Permission.DOCUMENT_WRITE,
    Permission.SOURCE_WRITE,
    Permission.EVIDENCE_WRITE,
    Permission.FEATURE_WRITE,
    Permission.MEMBER_WRITE,
})

ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ADMIN: frozenset(Permission),
    Role.DOCUMENT_AUTHOR: _READ | _WRITE,
    Role.REVIEWER: _READ | frozenset({Permission.DOCUMENT_REVIEW}),
    Role.APPROVER: _READ | frozenset({Permission.DOCUMENT_APPROVE}),
    Role.VIEWER: _READ,
}
