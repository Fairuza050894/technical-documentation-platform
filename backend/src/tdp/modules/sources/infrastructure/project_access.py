from tdp.modules.projects.domain.model import ProjectId, ProjectStatus
from tdp.modules.projects.domain.repository import ProjectRepository
from tdp.modules.workspaces.domain.model import WorkspaceId, WorkspaceStatus
from tdp.modules.workspaces.domain.repository import WorkspaceRepository


class RepositoryBackedProjectAccess:
    def __init__(
        self,
        repository: ProjectRepository,
        workspace_repository: WorkspaceRepository | None = None,
    ) -> None:
        self._repository = repository
        self._workspace_repository = workspace_repository

    async def exists(self, project_id: str) -> bool:
        return await self._repository.get(ProjectId.from_string(project_id)) is not None

    async def is_active(self, project_id: str) -> bool:
        project = await self._repository.get(ProjectId.from_string(project_id))
        if project is None or project.status is not ProjectStatus.ACTIVE:
            return False
        if self._workspace_repository is None:
            return True
        workspace = await self._workspace_repository.get(
            WorkspaceId.from_string(project.workspace_id)
        )
        return workspace is not None and workspace.status is WorkspaceStatus.ACTIVE
