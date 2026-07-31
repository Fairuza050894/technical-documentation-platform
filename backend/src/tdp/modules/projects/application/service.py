from tdp.modules.projects.application.commands import CreateProjectCommand
from tdp.modules.projects.application.dto import ProjectDto
from tdp.modules.projects.domain.errors import (
    InvalidOwnershipTypeError,
    InvalidWorkspaceTypeError,
    ProjectKeyAlreadyExistsError,
    ProjectNotFoundError,
)
from tdp.modules.projects.domain.model import (
    OwnershipType,
    Project,
    ProjectDescription,
    ProjectId,
    ProjectKey,
    ProjectName,
    WorkspaceType,
)
from tdp.modules.projects.domain.repository import ProjectRepository
from tdp.modules.workspaces.domain.errors import (
    WorkspaceArchivedError,
    WorkspaceNotFoundError,
)
from tdp.modules.workspaces.domain.model import (
    DEFAULT_WORKSPACE_ID,
    WorkspaceId,
    WorkspaceStatus,
)
from tdp.modules.workspaces.domain.repository import WorkspaceRepository


class ProjectApplicationService:
    def __init__(
        self,
        repository: ProjectRepository,
        workspace_repository: WorkspaceRepository | None = None,
    ) -> None:
        self._repository = repository
        self._workspace_repository = workspace_repository

    async def create(self, command: CreateProjectCommand) -> ProjectDto:
        key = ProjectKey(command.key)
        if await self._repository.get_by_key(key) is not None:
            raise ProjectKeyAlreadyExistsError(f"Project key {key} is already in use.")

        try:
            legacy_workspace_type = WorkspaceType(command.workspace_type)
        except ValueError as exc:
            raise InvalidWorkspaceTypeError(
                f"Workspace type {command.workspace_type} is not supported."
            ) from exc

        try:
            ownership_type = (
                OwnershipType(command.ownership_type)
                if command.ownership_type is not None
                else OwnershipType.from_legacy_workspace_type(legacy_workspace_type)
            )
        except ValueError as exc:
            raise InvalidOwnershipTypeError(
                f"Ownership type {command.ownership_type} is not supported."
            ) from exc

        workspace_id = command.workspace_id or DEFAULT_WORKSPACE_ID
        if self._workspace_repository is not None:
            workspace = await self._workspace_repository.get(WorkspaceId.from_string(workspace_id))
            if workspace is None:
                raise WorkspaceNotFoundError(f"Workspace {workspace_id} was not found.")
            if workspace.status is WorkspaceStatus.ARCHIVED:
                raise WorkspaceArchivedError(
                    f"Workspace {workspace_id} is archived and cannot receive new projects."
                )

        if command.ownership_type is not None:
            legacy_workspace_type = (
                WorkspaceType.ENTERPRISE
                if ownership_type is OwnershipType.TEAM
                else WorkspaceType.PERSONAL
            )

        project = Project.create(
            key=key,
            name=ProjectName(command.name),
            description=ProjectDescription(command.description),
            workspace_type=legacy_workspace_type,
            workspace_id=workspace_id,
            ownership_type=ownership_type,
        )
        await self._repository.add(project)
        return ProjectDto.from_domain(project)

    async def list_projects(self, workspace_id: str | None = None) -> list[ProjectDto]:
        if workspace_id is not None and self._workspace_repository is not None:
            workspace = await self._workspace_repository.get(WorkspaceId.from_string(workspace_id))
            if workspace is None:
                raise WorkspaceNotFoundError(f"Workspace {workspace_id} was not found.")

        projects = (
            await self._repository.list_all()
            if workspace_id is None
            else await self._repository.list_by_workspace(workspace_id)
        )
        return [ProjectDto.from_domain(project) for project in projects]

    async def get(self, project_id: str) -> ProjectDto:
        project = await self._repository.get(ProjectId.from_string(project_id))
        if project is None:
            raise ProjectNotFoundError(f"Project {project_id} was not found.")
        return ProjectDto.from_domain(project)

    async def archive(self, project_id: str) -> ProjectDto:
        project = await self._repository.get(ProjectId.from_string(project_id))
        if project is None:
            raise ProjectNotFoundError(f"Project {project_id} was not found.")
        if self._workspace_repository is not None:
            workspace = await self._workspace_repository.get(
                WorkspaceId.from_string(project.workspace_id)
            )
            if workspace is None:
                raise WorkspaceNotFoundError(f"Workspace {project.workspace_id} was not found.")
            if workspace.status is WorkspaceStatus.ARCHIVED:
                raise WorkspaceArchivedError(
                    f"Workspace {project.workspace_id} is archived and read-only."
                )
        project.archive()
        await self._repository.update(project)
        return ProjectDto.from_domain(project)
