import asyncio

from tdp.modules.projects.application.commands import CreateProjectCommand
from tdp.modules.projects.application.service import ProjectApplicationService
from tdp.modules.projects.domain.model import Project, ProjectId, ProjectKey


class InMemoryProjectRepository:
    def __init__(self) -> None:
        self.projects: dict[str, Project] = {}

    async def add(self, project: Project) -> None:
        self.projects[str(project.id)] = project

    async def update(self, project: Project) -> None:
        self.projects[str(project.id)] = project

    async def get(self, project_id: ProjectId) -> Project | None:
        return self.projects.get(str(project_id))

    async def get_by_key(self, key: ProjectKey) -> Project | None:
        return next(
            (project for project in self.projects.values() if project.key == key),
            None,
        )

    async def list_all(self) -> list[Project]:
        return list(self.projects.values())


def test_create_and_list_projects() -> None:
    repository = InMemoryProjectRepository()
    service = ProjectApplicationService(repository)

    created = asyncio.run(
        service.create(
            CreateProjectCommand(
                key="docs",
                name="Documentation Platform",
                description="Source-backed documentation",
                workspace_type="PERSONAL",
            )
        )
    )
    projects = asyncio.run(service.list_projects())

    assert created.key == "DOCS"
    assert projects == [created]


def test_archive_project() -> None:
    repository = InMemoryProjectRepository()
    service = ProjectApplicationService(repository)
    created = asyncio.run(
        service.create(
            CreateProjectCommand(
                key="docs",
                name="Documentation Platform",
                description="",
                workspace_type="PERSONAL",
            )
        )
    )

    archived = asyncio.run(service.archive(created.id))

    assert archived.status == "ARCHIVED"
