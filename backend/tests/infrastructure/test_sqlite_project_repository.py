import asyncio
from pathlib import Path

from tdp.modules.projects.domain.model import (
    Project,
    ProjectDescription,
    ProjectKey,
    ProjectName,
    WorkspaceType,
)
from tdp.modules.projects.infrastructure.sqlite_repository import SqliteProjectRepository


def test_repository_persists_project_between_instances(tmp_path: Path) -> None:
    database_path = tmp_path / "projects.sqlite3"
    first_repository = SqliteProjectRepository(database_path)
    project = Project.create(
        key=ProjectKey("DOCS"),
        name=ProjectName("Documentation Platform"),
        description=ProjectDescription("Persistent local project"),
        workspace_type=WorkspaceType.PERSONAL,
    )

    asyncio.run(first_repository.add(project))
    second_repository = SqliteProjectRepository(database_path)
    stored = asyncio.run(second_repository.get(project.id))

    assert stored is not None
    assert stored.key == project.key
    assert stored.name == project.name
