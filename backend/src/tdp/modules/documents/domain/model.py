import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from tdp.modules.documents.domain.errors import InvalidDocumentIdError


class DocumentType(StrEnum):
    TECHNICAL_SOURCE_OVERVIEW = "TECHNICAL_SOURCE_OVERVIEW"


class DocumentFormat(StrEnum):
    MARKDOWN = "MARKDOWN"


@dataclass(frozen=True, slots=True)
class DocumentId:
    value: UUID

    @classmethod
    def new(cls) -> "DocumentId":
        return cls(uuid4())

    @classmethod
    def from_string(cls, value: str) -> "DocumentId":
        try:
            return cls(UUID(value))
        except ValueError as exc:
            raise InvalidDocumentIdError("Document ID must be a valid UUID.") from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class GeneratedDocument:
    id: DocumentId
    project_id: str
    source_id: str
    target_run_id: str
    baseline_run_id: str | None
    document_type: DocumentType
    document_format: DocumentFormat
    title: str
    file_name: str
    content: str
    checksum: str
    operation_count: int
    schema_count: int
    breaking_change_count: int
    generated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        project_id: str,
        source_id: str,
        target_run_id: str,
        baseline_run_id: str | None,
        title: str,
        file_name: str,
        content: str,
        operation_count: int,
        schema_count: int,
        breaking_change_count: int,
        now: datetime | None = None,
    ) -> "GeneratedDocument":
        return cls(
            id=DocumentId.new(),
            project_id=project_id,
            source_id=source_id,
            target_run_id=target_run_id,
            baseline_run_id=baseline_run_id,
            document_type=DocumentType.TECHNICAL_SOURCE_OVERVIEW,
            document_format=DocumentFormat.MARKDOWN,
            title=title,
            file_name=file_name,
            content=content,
            checksum=hashlib.sha256(content.encode("utf-8")).hexdigest(),
            operation_count=operation_count,
            schema_count=schema_count,
            breaking_change_count=breaking_change_count,
            generated_at=now or datetime.now(UTC),
        )
