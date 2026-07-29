from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from tdp.modules.catalog.domain.errors import InvalidSynchronizationIdError


class SynchronizationStatus(StrEnum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class SynchronizationId:
    value: UUID

    @classmethod
    def new(cls) -> "SynchronizationId":
        return cls(uuid4())

    @classmethod
    def from_string(cls, value: str) -> "SynchronizationId":
        try:
            return cls(UUID(value))
        except ValueError as exc:
            raise InvalidSynchronizationIdError("Synchronization ID must be a valid UUID.") from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class ApiParameter:
    name: str
    location: str
    required: bool
    schema_type: str
    schema_format: str
    schema_reference: str


@dataclass(frozen=True, slots=True)
class ApiPayload:
    required: bool
    media_types: tuple[str, ...]
    schema_types: tuple[str, ...]
    schema_references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ApiResponse:
    status_code: str
    description: str
    media_types: tuple[str, ...]
    schema_types: tuple[str, ...]
    schema_references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ApiSchemaProperty:
    name: str
    schema_type: str
    schema_format: str
    required: bool
    reference: str
    description: str


@dataclass(frozen=True, slots=True)
class ApiOperation:
    synchronization_id: SynchronizationId
    project_id: str
    source_id: str
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
class ApiSchema:
    synchronization_id: SynchronizationId
    project_id: str
    source_id: str
    name: str
    schema_type: str
    description: str
    required_fields: tuple[str, ...]
    properties: tuple[ApiSchemaProperty, ...]
    source_pointer: str


@dataclass(slots=True)
class SynchronizationRun:
    id: SynchronizationId
    project_id: str
    source_id: str
    source_checksum: str
    status: SynchronizationStatus
    operation_count: int
    schema_count: int
    error_code: str
    error_message: str
    started_at: datetime
    completed_at: datetime | None

    @classmethod
    def start(
        cls,
        *,
        project_id: str,
        source_id: str,
        source_checksum: str,
        now: datetime | None = None,
    ) -> "SynchronizationRun":
        return cls(
            id=SynchronizationId.new(),
            project_id=project_id,
            source_id=source_id,
            source_checksum=source_checksum,
            status=SynchronizationStatus.RUNNING,
            operation_count=0,
            schema_count=0,
            error_code="",
            error_message="",
            started_at=now or datetime.now(UTC),
            completed_at=None,
        )

    def complete(
        self,
        *,
        operation_count: int,
        schema_count: int,
        now: datetime | None = None,
    ) -> None:
        self.status = SynchronizationStatus.COMPLETED
        self.operation_count = operation_count
        self.schema_count = schema_count
        self.error_code = ""
        self.error_message = ""
        self.completed_at = now or datetime.now(UTC)

    def fail(
        self,
        *,
        error_code: str,
        error_message: str,
        now: datetime | None = None,
    ) -> None:
        self.status = SynchronizationStatus.FAILED
        self.error_code = error_code
        self.error_message = error_message
        self.completed_at = now or datetime.now(UTC)
