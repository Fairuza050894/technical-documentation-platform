from dataclasses import dataclass
from typing import Protocol

from tdp.modules.catalog.domain.model import (
    ApiParameter,
    ApiPayload,
    ApiResponse,
    ApiSchemaProperty,
)


@dataclass(frozen=True, slots=True)
class ParsedOperation:
    method: str
    path: str
    operation_id: str
    summary: str
    description: str
    tags: tuple[str, ...]
    deprecated: bool
    security_schemes: tuple[str, ...]
    parameters: tuple[ApiParameter, ...]
    request_body: ApiPayload | None
    responses: tuple[ApiResponse, ...]
    source_pointer: str


@dataclass(frozen=True, slots=True)
class ParsedSchema:
    name: str
    schema_type: str
    description: str
    required_fields: tuple[str, ...]
    properties: tuple[ApiSchemaProperty, ...]
    source_pointer: str


@dataclass(frozen=True, slots=True)
class ParsedCatalog:
    operations: tuple[ParsedOperation, ...]
    schemas: tuple[ParsedSchema, ...]


class ArtifactReader(Protocol):
    async def read(self, artifact_key: str) -> bytes: ...


class OpenApiCatalogParser(Protocol):
    def parse(self, content: bytes) -> ParsedCatalog: ...


class ProjectCatalogAccess(Protocol):
    async def exists(self, project_id: str) -> bool: ...
