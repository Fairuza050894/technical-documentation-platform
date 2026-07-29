import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import PurePosixPath
from uuid import UUID, uuid4

from tdp.modules.sources.domain.errors import (
    InvalidArtifactKeyError,
    InvalidSourceChecksumError,
    InvalidSourceFileNameError,
    InvalidSourceIdError,
    InvalidSourceNameError,
    InvalidSourceProjectIdError,
    SourceAlreadyArchivedError,
)

_CHECKSUM_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_ALLOWED_FILE_SUFFIXES = {".json", ".yaml", ".yml"}


class SourceType(StrEnum):
    OPENAPI_FILE = "OPENAPI_FILE"


class SourceStatus(StrEnum):
    READY = "READY"
    ARCHIVED = "ARCHIVED"


class SourceMediaType(StrEnum):
    JSON = "JSON"
    YAML = "YAML"


@dataclass(frozen=True, slots=True)
class SourceId:
    value: UUID

    @classmethod
    def new(cls) -> "SourceId":
        return cls(uuid4())

    @classmethod
    def from_string(cls, value: str) -> "SourceId":
        try:
            return cls(UUID(value))
        except ValueError as exc:
            raise InvalidSourceIdError("Source ID must be a valid UUID.") from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class SourceProjectId:
    value: UUID

    @classmethod
    def from_string(cls, value: str) -> "SourceProjectId":
        try:
            return cls(UUID(value))
        except ValueError as exc:
            raise InvalidSourceProjectIdError("Project ID must be a valid UUID.") from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class SourceName:
    value: str

    def __post_init__(self) -> None:
        normalized = " ".join(self.value.split())
        if not 3 <= len(normalized) <= 80:
            raise InvalidSourceNameError("Source name must contain 3-80 characters.")
        object.__setattr__(self, "value", normalized)

    @property
    def comparison_key(self) -> str:
        return self.value.casefold()

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class SourceFileName:
    value: str

    def __post_init__(self) -> None:
        normalized = PurePosixPath(self.value.replace("\\", "/")).name.strip()
        if not normalized or len(normalized) > 160:
            raise InvalidSourceFileNameError("Source file name must contain 1-160 characters.")
        if PurePosixPath(normalized).suffix.lower() not in _ALLOWED_FILE_SUFFIXES:
            raise InvalidSourceFileNameError("OpenAPI source file must use .json, .yaml, or .yml.")
        object.__setattr__(self, "value", normalized)

    @property
    def suffix(self) -> str:
        return PurePosixPath(self.value).suffix.lower()

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class SourceChecksum:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not _CHECKSUM_PATTERN.fullmatch(normalized):
            raise InvalidSourceChecksumError("Source checksum must be a SHA-256 hexadecimal value.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ArtifactKey:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().replace("\\", "/")
        path = PurePosixPath(normalized)
        if not normalized or path.is_absolute() or ".." in path.parts:
            raise InvalidArtifactKeyError("Artifact key must be a safe relative path.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(slots=True)
class SourceConnection:
    id: SourceId
    project_id: SourceProjectId
    name: SourceName
    source_type: SourceType
    status: SourceStatus
    original_file_name: SourceFileName
    media_type: SourceMediaType
    checksum: SourceChecksum
    artifact_key: ArtifactKey
    openapi_version: str
    api_title: str
    api_version: str
    path_count: int
    operation_count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create_openapi_file(
        cls,
        *,
        source_id: SourceId,
        project_id: SourceProjectId,
        name: SourceName,
        original_file_name: SourceFileName,
        media_type: SourceMediaType,
        checksum: SourceChecksum,
        artifact_key: ArtifactKey,
        openapi_version: str,
        api_title: str,
        api_version: str,
        path_count: int,
        operation_count: int,
        now: datetime | None = None,
    ) -> "SourceConnection":
        created_at = now or datetime.now(UTC)
        return cls(
            id=source_id,
            project_id=project_id,
            name=name,
            source_type=SourceType.OPENAPI_FILE,
            status=SourceStatus.READY,
            original_file_name=original_file_name,
            media_type=media_type,
            checksum=checksum,
            artifact_key=artifact_key,
            openapi_version=openapi_version,
            api_title=api_title,
            api_version=api_version,
            path_count=path_count,
            operation_count=operation_count,
            created_at=created_at,
            updated_at=created_at,
        )

    def archive(self, *, now: datetime | None = None) -> None:
        if self.status is SourceStatus.ARCHIVED:
            raise SourceAlreadyArchivedError(f"Source {self.id} is already archived.")
        self.status = SourceStatus.ARCHIVED
        self.updated_at = now or datetime.now(UTC)
