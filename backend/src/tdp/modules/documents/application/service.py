import hashlib
import re

from tdp.modules.catalog.domain.model import SynchronizationId, SynchronizationStatus
from tdp.modules.catalog.domain.repository import CatalogRepository
from tdp.modules.changes.domain.model import DeterministicCatalogComparator
from tdp.modules.documents.application.commands import (
    CompareDocumentVersionsCommand,
    DocumentWorkflowCommand,
    GenerateTechnicalSourceOverviewCommand,
)
from tdp.modules.documents.application.dto import (
    DocumentDetailDto,
    DocumentSummaryDto,
    DocumentVersionComparisonDto,
    WorkflowEventDto,
)
from tdp.modules.documents.application.ports import (
    TechnicalSourceOverviewContext,
    TechnicalSourceOverviewRenderer,
)
from tdp.modules.documents.domain.comparison import DeterministicMarkdownSectionComparator
from tdp.modules.documents.domain.errors import (
    DocumentNotFoundError,
    DocumentProjectNotFoundError,
    DocumentSnapshotNotFoundError,
    DocumentSourceNotFoundError,
    DocumentVersionNotFoundError,
    InvalidDocumentGenerationError,
    InvalidDocumentVersionComparisonError,
)
from tdp.modules.documents.domain.model import (
    DocumentId,
    DocumentSeries,
    DocumentType,
    DocumentVersion,
    DocumentVersionId,
    DocumentVersionNumber,
)
from tdp.modules.documents.domain.repository import DocumentRepository
from tdp.modules.projects.domain.model import ProjectId
from tdp.modules.projects.domain.repository import ProjectRepository
from tdp.modules.sources.domain.model import SourceId
from tdp.modules.sources.domain.repository import SourceRepository


class DocumentApplicationService:
    def __init__(
        self,
        repository: DocumentRepository,
        project_repository: ProjectRepository,
        source_repository: SourceRepository,
        catalog_repository: CatalogRepository,
        comparator: DeterministicCatalogComparator,
        renderer: TechnicalSourceOverviewRenderer,
    ) -> None:
        self._repository = repository
        self._project_repository = project_repository
        self._source_repository = source_repository
        self._catalog_repository = catalog_repository
        self._comparator = comparator
        self._renderer = renderer
        self._document_comparator = DeterministicMarkdownSectionComparator()

    async def generate(
        self,
        command: GenerateTechnicalSourceOverviewCommand,
    ) -> DocumentDetailDto:
        project = await self._project_repository.get(ProjectId.from_string(command.project_id))
        if project is None:
            raise DocumentProjectNotFoundError(f"Project {command.project_id} was not found.")

        target = await self._catalog_repository.get_run(
            SynchronizationId.from_string(command.target_run_id)
        )
        if target is None:
            raise DocumentSnapshotNotFoundError(
                f"Synchronization {command.target_run_id} was not found."
            )
        if target.project_id != command.project_id:
            raise InvalidDocumentGenerationError(
                "The target synchronization does not belong to the selected project."
            )
        if target.status is not SynchronizationStatus.COMPLETED:
            raise InvalidDocumentGenerationError(
                "Technical Source Overview requires a completed target synchronization."
            )

        source = await self._source_repository.get(SourceId.from_string(target.source_id))
        if source is None:
            raise DocumentSourceNotFoundError(f"Source {target.source_id} was not found.")

        operations = await self._catalog_repository.list_operations_by_run(target.id)
        schemas = await self._catalog_repository.list_schemas_by_run(target.id)
        comparison = None

        if command.baseline_run_id is not None:
            if command.baseline_run_id == command.target_run_id:
                raise InvalidDocumentGenerationError(
                    "Baseline and target synchronizations must be different."
                )
            baseline = await self._catalog_repository.get_run(
                SynchronizationId.from_string(command.baseline_run_id)
            )
            if baseline is None:
                raise DocumentSnapshotNotFoundError(
                    f"Synchronization {command.baseline_run_id} was not found."
                )
            if baseline.project_id != command.project_id:
                raise InvalidDocumentGenerationError(
                    "The baseline synchronization does not belong to the selected project."
                )
            if baseline.status is not SynchronizationStatus.COMPLETED:
                raise InvalidDocumentGenerationError(
                    "Technical Source Overview requires a completed baseline synchronization."
                )

            comparison = self._comparator.compare(
                project_id=command.project_id,
                baseline_run_id=command.baseline_run_id,
                target_run_id=command.target_run_id,
                baseline_operations=await self._catalog_repository.list_operations_by_run(
                    baseline.id
                ),
                target_operations=operations,
                baseline_schemas=await self._catalog_repository.list_schemas_by_run(baseline.id),
                target_schemas=schemas,
            )

        context = TechnicalSourceOverviewContext(
            project=project,
            source=source,
            target_run=target,
            operations=tuple(operations),
            schemas=tuple(schemas),
            comparison=comparison,
        )
        content = self._renderer.render(context)
        checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()
        title = f"Technical Source Overview — {source.api_title}"
        series = await self._repository.get_series_by_project_type(
            command.project_id,
            DocumentType.TECHNICAL_SOURCE_OVERVIEW,
        )
        if series is None:
            series = DocumentSeries.create(
                project_id=command.project_id,
                document_type=DocumentType.TECHNICAL_SOURCE_OVERVIEW,
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
            source_id=target.source_id,
            target_run_id=command.target_run_id,
            baseline_run_id=command.baseline_run_id,
            version_number=version_number,
            title=title,
            file_name=self._file_name(
                str(project.key),
                str(source.name),
                version_number,
            ),
            content=content,
            operation_count=len(operations),
            schema_count=len(schemas),
            breaking_change_count=(comparison.breaking_total if comparison is not None else 0),
            revision_reason=command.revision_reason,
            created_by=command.actor,
        )
        series.register_version(version.id, now=version.created_at)
        await self._repository.add_version(series, version, version.generated_event())
        return DocumentDetailDto.from_domain(version)

    async def list_documents(self, project_id: str) -> list[DocumentSummaryDto]:
        project = await self._project_repository.get(ProjectId.from_string(project_id))
        if project is None:
            raise DocumentProjectNotFoundError(f"Project {project_id} was not found.")
        versions = await self._repository.list_versions_by_project(project_id)
        return [DocumentSummaryDto.from_domain(version) for version in versions]

    async def list_versions(self, document_id: str) -> list[DocumentSummaryDto]:
        series = await self._repository.get_series(DocumentId.from_string(document_id))
        if series is None:
            raise DocumentNotFoundError(f"Document {document_id} was not found.")
        versions = await self._repository.list_versions(series.id)
        return [DocumentSummaryDto.from_domain(version) for version in versions]

    async def get_document(self, version_id: str) -> DocumentDetailDto:
        return await self.get_version(version_id)

    async def get_version(self, version_id: str) -> DocumentDetailDto:
        version = await self._require_version(version_id)
        return DocumentDetailDto.from_domain(version)

    async def submit_for_review(
        self,
        command: DocumentWorkflowCommand,
    ) -> DocumentDetailDto:
        version, series = await self._require_version_and_series(command.version_id)
        event = version.submit_for_review(actor=command.actor, comment=command.comment)
        await self._repository.apply_workflow_transition(series, version, event)
        return DocumentDetailDto.from_domain(version)

    async def request_changes(
        self,
        command: DocumentWorkflowCommand,
    ) -> DocumentDetailDto:
        version, series = await self._require_version_and_series(command.version_id)
        event = version.request_changes(actor=command.actor, comment=command.comment)
        await self._repository.apply_workflow_transition(series, version, event)
        return DocumentDetailDto.from_domain(version)

    async def approve(
        self,
        command: DocumentWorkflowCommand,
    ) -> DocumentDetailDto:
        version, series = await self._require_version_and_series(command.version_id)
        event = version.approve(actor=command.actor, comment=command.comment)
        previous_approved = await self._repository.get_current_approved_version(series.id)
        superseded_version = None
        superseded_event = None
        if previous_approved is not None and previous_approved.id != version.id:
            superseded_version = previous_approved
            superseded_event = previous_approved.supersede(
                actor=command.actor,
                comment=f"Superseded by approved version {version.version_number}.",
                now=version.approved_at,
            )
        series.register_approved_version(version.id, now=version.approved_at)
        await self._repository.apply_workflow_transition(
            series,
            version,
            event,
            superseded_version=superseded_version,
            superseded_event=superseded_event,
        )
        return DocumentDetailDto.from_domain(version)

    async def supersede(
        self,
        command: DocumentWorkflowCommand,
    ) -> DocumentDetailDto:
        version, series = await self._require_version_and_series(command.version_id)
        event = version.supersede(actor=command.actor, comment=command.comment)
        if series.current_approved_version_id == str(version.id):
            series.clear_approved_version(now=version.superseded_at)
        await self._repository.apply_workflow_transition(series, version, event)
        return DocumentDetailDto.from_domain(version)

    async def compare_versions(
        self,
        command: CompareDocumentVersionsCommand,
    ) -> DocumentVersionComparisonDto:
        baseline = await self._require_version(command.baseline_version_id)
        target = await self._require_version(command.target_version_id)
        if baseline.document_id != target.document_id:
            raise InvalidDocumentVersionComparisonError(
                "Document versions must belong to the same document series."
            )

        comparison = self._document_comparator.compare(
            baseline_version_id=str(baseline.id),
            target_version_id=str(target.id),
            document_id=str(target.document_id),
            baseline_content=baseline.content,
            target_content=target.content,
        )
        return DocumentVersionComparisonDto.from_domain(comparison)

    async def list_workflow_events(self, version_id: str) -> list[WorkflowEventDto]:
        version = await self._require_version(version_id)
        events = await self._repository.list_workflow_events(version.id)
        return [WorkflowEventDto.from_domain(event) for event in events]

    async def _require_version(self, version_id: str) -> DocumentVersion:
        version = await self._repository.get_version(DocumentVersionId.from_string(version_id))
        if version is None:
            raise DocumentVersionNotFoundError(f"Document version {version_id} was not found.")
        return version

    async def _require_version_and_series(
        self,
        version_id: str,
    ) -> tuple[DocumentVersion, DocumentSeries]:
        version = await self._require_version(version_id)
        series = await self._repository.get_series(version.document_id)
        if series is None:
            raise DocumentNotFoundError(f"Document {version.document_id} was not found.")
        return version, series

    @staticmethod
    def _file_name(
        project_key: str,
        source_name: str,
        version_number: DocumentVersionNumber,
    ) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", source_name.casefold()).strip("-")
        source_slug = slug or "source"
        return (
            f"{project_key.casefold()}-{source_slug}-technical-source-overview-v{version_number}.md"
        )
