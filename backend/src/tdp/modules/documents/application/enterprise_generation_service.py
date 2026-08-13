import hashlib

from tdp.modules.documents.application.commands import GenerateEnterpriseDocumentCommand
from tdp.modules.documents.application.dto import DocumentDetailDto
from tdp.modules.documents.application.enterprise_generation_ports import (
    EnterpriseDocumentRenderer,
    EnterpriseGenerationInputProvider,
)
from tdp.modules.documents.domain.errors import (
    EnterpriseDocumentGenerationBlockedError,
    UnsupportedEnterpriseDocumentProfileError,
)
from tdp.modules.documents.domain.generation import enterprise_generation_profile
from tdp.modules.documents.domain.model import (
    DocumentProvenanceReference,
    DocumentSeries,
    DocumentType,
    DocumentVersion,
    DocumentVersionNumber,
)
from tdp.modules.documents.domain.repository import DocumentRepository


class EnterpriseDocumentGenerationService:
    def __init__(
        self,
        repository: DocumentRepository,
        input_provider: EnterpriseGenerationInputProvider,
        renderer: EnterpriseDocumentRenderer,
    ) -> None:
        self._repository = repository
        self._input_provider = input_provider
        self._renderer = renderer

    async def generate(
        self,
        command: GenerateEnterpriseDocumentCommand,
    ) -> DocumentDetailDto:
        document_type = _document_type(command.document_type)
        profile = enterprise_generation_profile(document_type)
        if profile is None:
            raise UnsupportedEnterpriseDocumentProfileError(
                f"{document_type.value} does not have a deterministic generation profile yet."
            )

        readiness = await self._input_provider.readiness(command.project_id, profile)
        if not readiness.eligible:
            raise EnterpriseDocumentGenerationBlockedError(
                document_type=document_type.value,
                readiness_state=readiness.state,
                policy_version=readiness.policy_version,
                findings=readiness.findings,
            )

        context = await self._input_provider.collect(command.project_id, profile)
        content = self._renderer.render(context)
        checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()
        title = f"{profile.display_name} — {context.project_name}"

        series = await self._repository.get_series_by_project_type(
            command.project_id,
            document_type,
        )
        if series is None:
            series = DocumentSeries.create(
                project_id=command.project_id,
                document_type=document_type,
                title=title,
            )
        else:
            duplicate = await self._repository.find_version_by_checksum(series.id, checksum)
            if duplicate is not None:
                return DocumentDetailDto.from_domain(
                    duplicate,
                    reused_existing_version=True,
                )
            series.title = title

        previous_versions = await self._repository.list_versions(series.id)
        version_number = (
            previous_versions[0].version_number.next_minor()
            if previous_versions
            else DocumentVersionNumber.first()
        )
        version = DocumentVersion.create(
            document_id=series.id,
            project_id=command.project_id,
            source_id=context.source_id,
            target_run_id=context.target_run_id,
            baseline_run_id=None,
            version_number=version_number,
            title=title,
            file_name=_file_name(context.project_key, profile.file_slug, version_number),
            content=content,
            operation_count=len(context.operations),
            schema_count=len(context.schemas),
            breaking_change_count=0,
            revision_reason=command.revision_reason,
            created_by=command.principal.audit_actor,
            document_type=document_type,
            provenance=tuple(
                DocumentProvenanceReference.evidence_artifact(
                    evidence_id=item.id,
                    evidence_kind=item.kind,
                    checksum=item.checksum,
                )
                for item in context.evidence
            ),
        )
        series.register_version(version.id, now=version.created_at)
        await self._repository.add_version(series, version, version.generated_event())
        return DocumentDetailDto.from_domain(version)


def _document_type(value: str) -> DocumentType:
    try:
        return DocumentType(value.strip().upper())
    except ValueError as exc:
        raise UnsupportedEnterpriseDocumentProfileError(
            f"{value} is not a recognized Project document type."
        ) from exc


def _file_name(
    project_key: str,
    file_slug: str,
    version_number: DocumentVersionNumber,
) -> str:
    return f"{project_key.casefold()}-{file_slug}-v{version_number}.md"
