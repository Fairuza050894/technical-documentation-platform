from tdp.modules.projects.application.commands import CreateProjectCommand
from tdp.modules.projects.application.dto import ProjectDto
from tdp.modules.projects.domain.errors import (
    InvalidWorkspaceTypeError,
    ProjectKeyAlreadyExistsError,
    ProjectNotFoundError,
)
from tdp.modules.projects.domain.model import (
    Project,
    ProjectDescription,
    ProjectId,
    ProjectKey,
    ProjectName,
    WorkspaceType,
)
from tdp.modules.projects.domain.repository import ProjectRepository


class ProjectApplicationService:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    async def create(self, command: CreateProjectCommand) -> ProjectDto:
        key = ProjectKey(command.key)
        if await self._repository.get_by_key(key) is not None:
            raise ProjectKeyAlreadyExistsError(f"Project key {key} is already in use.")

        try:
            workspace_type = WorkspaceType(command.workspace_type)
        except ValueError as exc:
            raise InvalidWorkspaceTypeError(
                f"Workspace type {command.workspace_type} is not supported."
            ) from exc

        project = Project.create(
            key=key,
            name=ProjectName(command.name),
            description=ProjectDescription(command.description),
            workspace_type=workspace_type,
        )
        await self._repository.add(project)
        return ProjectDto.from_domain(project)

    async def list_projects(self) -> list[ProjectDto]:
        projects = await self._repository.list_all()
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
        project.archive()
        await self._repository.update(project)
        return ProjectDto.from_domain(project)
