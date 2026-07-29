from dataclasses import asdict, dataclass
from typing import Any

from tdp.modules.catalog.domain.model import ApiOperation, ApiSchema, SynchronizationRun


@dataclass(frozen=True, slots=True)
class SynchronizationDto:
    id: str
    project_id: str
    source_id: str
    source_checksum: str
    status: str
    operation_count: int
    schema_count: int
    error_code: str
    error_message: str
    started_at: str
    completed_at: str | None

    @classmethod
    def from_domain(cls, run: SynchronizationRun) -> "SynchronizationDto":
        return cls(
            id=str(run.id),
            project_id=run.project_id,
            source_id=run.source_id,
            source_checksum=run.source_checksum,
            status=run.status.value,
            operation_count=run.operation_count,
            schema_count=run.schema_count,
            error_code=run.error_code,
            error_message=run.error_message,
            started_at=run.started_at.isoformat(),
            completed_at=run.completed_at.isoformat() if run.completed_at is not None else None,
        )


@dataclass(frozen=True, slots=True)
class ApiOperationDto:
    synchronization_id: str
    project_id: str
    source_id: str
    method: str
    path: str
    operation_id: str
    summary: str
    description: str
    tags: list[str]
    deprecated: bool
    security_schemes: list[str]
    parameters: list[dict[str, Any]]
    request_body: dict[str, Any] | None
    responses: list[dict[str, Any]]
    source_pointer: str

    @classmethod
    def from_domain(cls, operation: ApiOperation) -> "ApiOperationDto":
        return cls(
            synchronization_id=str(operation.synchronization_id),
            project_id=operation.project_id,
            source_id=operation.source_id,
            method=operation.method,
            path=operation.path,
            operation_id=operation.operation_id,
            summary=operation.summary,
            description=operation.description,
            tags=list(operation.tags),
            deprecated=operation.deprecated,
            security_schemes=list(operation.security_schemes),
            parameters=[asdict(parameter) for parameter in operation.parameters],
            request_body=(
                asdict(operation.request_body) if operation.request_body is not None else None
            ),
            responses=[asdict(response) for response in operation.responses],
            source_pointer=operation.source_pointer,
        )


@dataclass(frozen=True, slots=True)
class ApiSchemaDto:
    synchronization_id: str
    project_id: str
    source_id: str
    name: str
    schema_type: str
    description: str
    required_fields: list[str]
    properties: list[dict[str, Any]]
    source_pointer: str

    @classmethod
    def from_domain(cls, schema: ApiSchema) -> "ApiSchemaDto":
        return cls(
            synchronization_id=str(schema.synchronization_id),
            project_id=schema.project_id,
            source_id=schema.source_id,
            name=schema.name,
            schema_type=schema.schema_type,
            description=schema.description,
            required_fields=list(schema.required_fields),
            properties=[asdict(property_item) for property_item in schema.properties],
            source_pointer=schema.source_pointer,
        )


@dataclass(frozen=True, slots=True)
class CatalogDto:
    runs: list[SynchronizationDto]
    operations: list[ApiOperationDto]
    schemas: list[ApiSchemaDto]
