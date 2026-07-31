import asyncio

from tdp.modules.workspaces.application.commands import CreateWorkspaceCommand
from tdp.modules.workspaces.application.service import WorkspaceApplicationService
from tdp.modules.workspaces.domain.model import Workspace, WorkspaceId, WorkspaceKey


class InMemoryWorkspaceRepository:
    def __init__(self) -> None:
        default = Workspace.default()
        self.workspaces: dict[str, Workspace] = {str(default.id): default}

    async def add(self, workspace: Workspace) -> None:
        self.workspaces[str(workspace.id)] = workspace

    async def update(self, workspace: Workspace) -> None:
        self.workspaces[str(workspace.id)] = workspace

    async def get(self, workspace_id: WorkspaceId) -> Workspace | None:
        return self.workspaces.get(str(workspace_id))

    async def get_by_key(self, key: WorkspaceKey) -> Workspace | None:
        return next(
            (workspace for workspace in self.workspaces.values() if workspace.key == key),
            None,
        )

    async def list_all(self) -> list[Workspace]:
        return list(self.workspaces.values())


def test_create_and_list_workspaces() -> None:
    repository = InMemoryWorkspaceRepository()
    service = WorkspaceApplicationService(repository)

    created = asyncio.run(
        service.create(
            CreateWorkspaceCommand(
                key="erp",
                name="ERP Workspace",
                description="ERP systems and integrations",
            )
        )
    )
    workspaces = asyncio.run(service.list_workspaces())

    assert created.key == "ERP"
    assert created.status == "ACTIVE"
    assert any(workspace.id == created.id for workspace in workspaces)
