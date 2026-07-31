from tdp.modules.workspaces.application.commands import CreateWorkspaceCommand
from tdp.modules.workspaces.application.dto import WorkspaceDto
from tdp.modules.workspaces.domain.errors import (
    WorkspaceKeyAlreadyExistsError,
    WorkspaceNotFoundError,
)
from tdp.modules.workspaces.domain.model import (
    Workspace,
    WorkspaceDescription,
    WorkspaceId,
    WorkspaceKey,
    WorkspaceName,
)
from tdp.modules.workspaces.domain.repository import WorkspaceRepository


class WorkspaceApplicationService:
    def __init__(self, repository: WorkspaceRepository) -> None:
        self._repository = repository

    async def create(self, command: CreateWorkspaceCommand) -> WorkspaceDto:
        key = WorkspaceKey(command.key)
        if await self._repository.get_by_key(key) is not None:
            raise WorkspaceKeyAlreadyExistsError(f"Workspace key {key} is already in use.")

        workspace = Workspace.create(
            key=key,
            name=WorkspaceName(command.name),
            description=WorkspaceDescription(command.description),
        )
        await self._repository.add(workspace)
        return WorkspaceDto.from_domain(workspace)

    async def list_workspaces(self) -> list[WorkspaceDto]:
        workspaces = await self._repository.list_all()
        return [WorkspaceDto.from_domain(workspace) for workspace in workspaces]

    async def get(self, workspace_id: str) -> WorkspaceDto:
        workspace = await self._repository.get(WorkspaceId.from_string(workspace_id))
        if workspace is None:
            raise WorkspaceNotFoundError(f"Workspace {workspace_id} was not found.")
        return WorkspaceDto.from_domain(workspace)

    async def archive(self, workspace_id: str) -> WorkspaceDto:
        workspace = await self._repository.get(WorkspaceId.from_string(workspace_id))
        if workspace is None:
            raise WorkspaceNotFoundError(f"Workspace {workspace_id} was not found.")
        workspace.archive()
        await self._repository.update(workspace)
        return WorkspaceDto.from_domain(workspace)
