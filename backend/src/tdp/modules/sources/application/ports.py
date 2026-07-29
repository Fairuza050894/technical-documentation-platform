from dataclasses import dataclass
from typing import Protocol

from tdp.modules.sources.domain.model import SourceFileName, SourceId, SourceMediaType


@dataclass(frozen=True, slots=True)
class OpenApiInspection:
    media_type: SourceMediaType
    checksum: str
    openapi_version: str
    api_title: str
    api_version: str
    path_count: int
    operation_count: int


@dataclass(frozen=True, slots=True)
class StoredArtifact:
    key: str


class OpenApiInspector(Protocol):
    def inspect(self, file_name: SourceFileName, content: bytes) -> OpenApiInspection: ...


class ArtifactStore(Protocol):
    async def save(
        self,
        source_id: SourceId,
        file_name: SourceFileName,
        content: bytes,
    ) -> StoredArtifact: ...

    async def delete(self, artifact_key: str) -> None: ...


class ProjectAccessPort(Protocol):
    async def exists(self, project_id: str) -> bool: ...

    async def is_active(self, project_id: str) -> bool: ...
