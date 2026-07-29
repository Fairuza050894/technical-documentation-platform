from tdp.modules.projects.domain.model import ProjectId, ProjectStatus
from tdp.modules.projects.domain.repository import ProjectRepository


class RepositoryBackedProjectAccess:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    async def exists(self, project_id: str) -> bool:
        return await self._repository.get(ProjectId.from_string(project_id)) is not None

    async def is_active(self, project_id: str) -> bool:
        project = await self._repository.get(ProjectId.from_string(project_id))
        return project is not None and project.status is ProjectStatus.ACTIVE
