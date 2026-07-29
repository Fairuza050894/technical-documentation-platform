from dataclasses import dataclass

from tdp.modules.documents.domain.model import DocumentVersion, DocumentWorkflowEvent


@dataclass(frozen=True, slots=True)
class DocumentSummaryDto:
    id: str
    document_id: str
    project_id: str
    source_id: str
    target_run_id: str
    baseline_run_id: str | None
    document_type: str
    document_format: str
    version: str
    status: str
    title: str
    file_name: str
    checksum: str
    operation_count: int
    schema_count: int
    breaking_change_count: int
    revision_reason: str
    created_by: str
    generated_at: str
    updated_at: str
    submitted_at: str | None
    approved_at: str | None
    superseded_at: str | None

    @classmethod
    def from_domain(cls, version: DocumentVersion) -> "DocumentSummaryDto":
        return cls(
            id=str(version.id),
            document_id=str(version.document_id),
            project_id=version.project_id,
            source_id=version.source_id,
            target_run_id=version.target_run_id,
            baseline_run_id=version.baseline_run_id,
            document_type=version.document_type.value,
            document_format=version.document_format.value,
            version=str(version.version_number),
            status=version.status.value,
            title=version.title,
            file_name=version.file_name,
            checksum=version.checksum,
            operation_count=version.operation_count,
            schema_count=version.schema_count,
            breaking_change_count=version.breaking_change_count,
            revision_reason=version.revision_reason,
            created_by=version.created_by,
            generated_at=version.created_at.isoformat(),
            updated_at=version.updated_at.isoformat(),
            submitted_at=(
                version.submitted_at.isoformat() if version.submitted_at is not None else None
            ),
            approved_at=(
                version.approved_at.isoformat() if version.approved_at is not None else None
            ),
            superseded_at=(
                version.superseded_at.isoformat() if version.superseded_at is not None else None
            ),
        )


@dataclass(frozen=True, slots=True)
class DocumentDetailDto(DocumentSummaryDto):
    content: str
    reused_existing_version: bool

    @classmethod
    def from_domain(
        cls,
        version: DocumentVersion,
        *,
        reused_existing_version: bool = False,
    ) -> "DocumentDetailDto":
        summary = DocumentSummaryDto.from_domain(version)
        return cls(
            id=summary.id,
            document_id=summary.document_id,
            project_id=summary.project_id,
            source_id=summary.source_id,
            target_run_id=summary.target_run_id,
            baseline_run_id=summary.baseline_run_id,
            document_type=summary.document_type,
            document_format=summary.document_format,
            version=summary.version,
            status=summary.status,
            title=summary.title,
            file_name=summary.file_name,
            checksum=summary.checksum,
            operation_count=summary.operation_count,
            schema_count=summary.schema_count,
            breaking_change_count=summary.breaking_change_count,
            revision_reason=summary.revision_reason,
            created_by=summary.created_by,
            generated_at=summary.generated_at,
            updated_at=summary.updated_at,
            submitted_at=summary.submitted_at,
            approved_at=summary.approved_at,
            superseded_at=summary.superseded_at,
            content=version.content,
            reused_existing_version=reused_existing_version,
        )


@dataclass(frozen=True, slots=True)
class WorkflowEventDto:
    id: str
    version_id: str
    actor: str
    action: str
    previous_status: str | None
    new_status: str
    comment: str
    created_at: str

    @classmethod
    def from_domain(cls, event: DocumentWorkflowEvent) -> "WorkflowEventDto":
        return cls(
            id=str(event.id),
            version_id=str(event.version_id),
            actor=event.actor,
            action=event.action.value,
            previous_status=(
                event.previous_status.value if event.previous_status is not None else None
            ),
            new_status=event.new_status.value,
            comment=event.comment,
            created_at=event.created_at.isoformat(),
        )
