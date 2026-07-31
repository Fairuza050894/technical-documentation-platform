from datetime import UTC, datetime

import pytest

from tdp.modules.workspaces.domain.errors import DefaultWorkspaceArchiveError
from tdp.modules.workspaces.domain.model import (
    DEFAULT_WORKSPACE_ID,
    Workspace,
    WorkspaceDescription,
    WorkspaceKey,
    WorkspaceName,
    WorkspaceStatus,
)


def test_workspace_creation_normalizes_identity() -> None:
    created_at = datetime(2026, 7, 30, tzinfo=UTC)
    workspace = Workspace.create(
        key=WorkspaceKey("erp"),
        name=WorkspaceName("  ERP Platform  "),
        description=WorkspaceDescription("Operational systems"),
        now=created_at,
    )

    assert str(workspace.key) == "ERP"
    assert str(workspace.name) == "ERP Platform"
    assert workspace.status is WorkspaceStatus.ACTIVE
    assert workspace.created_at == created_at


def test_default_workspace_cannot_be_archived() -> None:
    workspace = Workspace.default()

    assert str(workspace.id) == DEFAULT_WORKSPACE_ID
    with pytest.raises(DefaultWorkspaceArchiveError):
        workspace.archive()
