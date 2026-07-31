import asyncio
from pathlib import Path

from tdp.modules.workspaces.domain.model import (
    DEFAULT_WORKSPACE_ID,
    Workspace,
    WorkspaceDescription,
    WorkspaceKey,
    WorkspaceName,
)
from tdp.modules.workspaces.infrastructure.sqlite_repository import (
    SqliteWorkspaceRepository,
)


def test_repository_creates_default_and_persists_workspace(tmp_path: Path) -> None:
    database_path = tmp_path / "workspaces.sqlite3"
    first_repository = SqliteWorkspaceRepository(database_path)

    default = asyncio.run(first_repository.list_all())[0]
    assert str(default.id) == DEFAULT_WORKSPACE_ID

    workspace = Workspace.create(
        key=WorkspaceKey("ERP"),
        name=WorkspaceName("ERP Workspace"),
        description=WorkspaceDescription("ERP systems"),
    )
    asyncio.run(first_repository.add(workspace))

    second_repository = SqliteWorkspaceRepository(database_path)
    stored = asyncio.run(second_repository.get(workspace.id))

    assert stored is not None
    assert stored.key == workspace.key
    assert stored.name == workspace.name
