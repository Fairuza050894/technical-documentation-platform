from dataclasses import dataclass

from tdp.modules.documents.domain.model import GeneratedDocument


@dataclass(frozen=True, slots=True)
class DocumentSummaryDto:
    id: str
    project_id: str
    source_id: str
    target_run_id: str
    baseline_run_id: str | None
    document_type: str
    document_format: str
    title: str
    file_name: str
    checksum: str
    operation_count: int
    schema_count: int
    breaking_change_count: int
    generated_at: str

    @classmethod
    def from_domain(cls, document: GeneratedDocument) -> "DocumentSummaryDto":
        return cls(
            id=str(document.id),
            project_id=document.project_id,
            source_id=document.source_id,
            target_run_id=document.target_run_id,
            baseline_run_id=document.baseline_run_id,
            document_type=document.document_type.value,
            document_format=document.document_format.value,
            title=document.title,
            file_name=document.file_name,
            checksum=document.checksum,
            operation_count=document.operation_count,
            schema_count=document.schema_count,
            breaking_change_count=document.breaking_change_count,
            generated_at=document.generated_at.isoformat(),
        )


@dataclass(frozen=True, slots=True)
class DocumentDetailDto(DocumentSummaryDto):
    content: str

    @classmethod
    def from_domain(cls, document: GeneratedDocument) -> "DocumentDetailDto":
        summary = DocumentSummaryDto.from_domain(document)
        return cls(
            id=summary.id,
            project_id=summary.project_id,
            source_id=summary.source_id,
            target_run_id=summary.target_run_id,
            baseline_run_id=summary.baseline_run_id,
            document_type=summary.document_type,
            document_format=summary.document_format,
            title=summary.title,
            file_name=summary.file_name,
            checksum=summary.checksum,
            operation_count=summary.operation_count,
            schema_count=summary.schema_count,
            breaking_change_count=summary.breaking_change_count,
            generated_at=summary.generated_at,
            content=document.content,
        )
