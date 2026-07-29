import asyncio

import pytest

from tdp.modules.sources.application.commands import ImportOpenApiSourceCommand
from tdp.modules.sources.application.ports import OpenApiInspection, StoredArtifact
from tdp.modules.sources.application.service import SourceApplicationService
from tdp.modules.sources.domain.errors import (
    SourceNameAlreadyExistsError,
    SourceProjectArchivedError,
)
from tdp.modules.sources.domain.model import (
    SourceConnection,
    SourceId,
    SourceMediaType,
    SourceName,
    SourceProjectId,
)


class InMemorySourceRepository:
    def __init__(self) -> None:
        self.sources: dict[str, SourceConnection] = {}

    async def add(self, source: SourceConnection) -> None:
        self.sources[str(source.id)] = source

    async def update(self, source: SourceConnection) -> None:
        self.sources[str(source.id)] = source

    async def get(self, source_id: SourceId) -> SourceConnection | None:
        return self.sources.get(str(source_id))

    async def get_by_name(
        self,
        project_id: SourceProjectId,
        name: SourceName,
    ) -> SourceConnection | None:
        return next(
            (
                source
                for source in self.sources.values()
                if source.project_id == project_id
                and source.name.comparison_key == name.comparison_key
            ),
            None,
        )

    async def list_by_project(self, project_id: SourceProjectId) -> list[SourceConnection]:
        return [source for source in self.sources.values() if source.project_id == project_id]


class StubProjectAccess:
    def __init__(self, *, active: bool = True) -> None:
        self.active = active

    async def exists(self, project_id: str) -> bool:
        return True

    async def is_active(self, project_id: str) -> bool:
        return self.active


class StubInspector:
    def inspect(self, file_name: object, content: bytes) -> OpenApiInspection:
        return OpenApiInspection(
            media_type=SourceMediaType.YAML,
            checksum="a" * 64,
            openapi_version="3.1.0",
            api_title="Commerce API",
            api_version="1.0.0",
            path_count=1,
            operation_count=2,
        )


class InMemoryArtifactStore:
    def __init__(self) -> None:
        self.saved: dict[str, bytes] = {}

    async def save(self, source_id: SourceId, file_name: object, content: bytes) -> StoredArtifact:
        key = f"{source_id}/source.yaml"
        self.saved[key] = content
        return StoredArtifact(key=key)

    async def delete(self, artifact_key: str) -> None:
        self.saved.pop(artifact_key, None)


def build_service(*, active: bool = True) -> SourceApplicationService:
    return SourceApplicationService(
        InMemorySourceRepository(),
        StubProjectAccess(active=active),
        StubInspector(),
        InMemoryArtifactStore(),
        max_file_bytes=1024,
    )


def command() -> ImportOpenApiSourceCommand:
    return ImportOpenApiSourceCommand(
        project_id="5e742f10-bdc0-4a24-b6dd-3002e875cc85",
        name="Commerce API",
        file_name="commerce.yaml",
        content=b"openapi: 3.1.0",
    )


def test_import_and_list_openapi_source() -> None:
    service = build_service()

    imported = asyncio.run(service.import_openapi(command()))
    sources = asyncio.run(service.list_sources(command().project_id))

    assert imported.api_title == "Commerce API"
    assert imported.operation_count == 2
    assert sources == [imported]


def test_duplicate_source_name_is_rejected_case_insensitively() -> None:
    service = build_service()
    asyncio.run(service.import_openapi(command()))

    duplicate = ImportOpenApiSourceCommand(
        project_id=command().project_id,
        name="commerce api",
        file_name="other.yaml",
        content=b"openapi: 3.1.0",
    )

    with pytest.raises(SourceNameAlreadyExistsError):
        asyncio.run(service.import_openapi(duplicate))


def test_archived_project_rejects_new_source() -> None:
    service = build_service(active=False)

    with pytest.raises(SourceProjectArchivedError):
        asyncio.run(service.import_openapi(command()))
