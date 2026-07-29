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
from tdp.modules.sources.domain.model import (
    ArtifactKey,
    SourceChecksum,
    SourceConnection,
    SourceFileName,
    SourceId,
    SourceMediaType,
    SourceName,
    SourceProjectId,
)
from tdp.modules.sources.infrastructure.sqlite_repository import SqliteSourceRepository


def test_repository_persists_source_between_instances(tmp_path: Path) -> None:
    database_path = tmp_path / "sources.sqlite3"
    project_repository = SqliteProjectRepository(database_path)
    project = Project.create(
        key=ProjectKey("DOCS"),
        name=ProjectName("Documentation Platform"),
        description=ProjectDescription(""),
        workspace_type=WorkspaceType.PERSONAL,
    )
    asyncio.run(project_repository.add(project))

    source = SourceConnection.create_openapi_file(
        source_id=SourceId.new(),
        project_id=SourceProjectId.from_string(str(project.id)),
        name=SourceName("Commerce API"),
        original_file_name=SourceFileName("commerce.yaml"),
        media_type=SourceMediaType.YAML,
        checksum=SourceChecksum("b" * 64),
        artifact_key=ArtifactKey(f"{project.id}/source.yaml"),
        openapi_version="3.1.0",
        api_title="Commerce API",
        api_version="1.0.0",
        path_count=1,
        operation_count=2,
    )
    first_repository = SqliteSourceRepository(database_path)
    asyncio.run(first_repository.add(source))

    second_repository = SqliteSourceRepository(database_path)
    stored = asyncio.run(second_repository.get(source.id))

    assert stored is not None
    assert stored.name == source.name
    assert stored.operation_count == 2
