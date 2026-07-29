import re

from tdp.modules.catalog.domain.model import SynchronizationId, SynchronizationStatus
from tdp.modules.catalog.domain.repository import CatalogRepository
from tdp.modules.changes.domain.model import DeterministicCatalogComparator
from tdp.modules.documents.application.commands import GenerateTechnicalSourceOverviewCommand
from tdp.modules.documents.application.dto import DocumentDetailDto, DocumentSummaryDto
from tdp.modules.documents.application.ports import (
    TechnicalSourceOverviewContext,
    TechnicalSourceOverviewRenderer,
)
from tdp.modules.documents.domain.errors import (
    DocumentNotFoundError,
    DocumentProjectNotFoundError,
    DocumentSnapshotNotFoundError,
    DocumentSourceNotFoundError,
    InvalidDocumentGenerationError,
)
from tdp.modules.documents.domain.model import DocumentId, GeneratedDocument
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
        document = GeneratedDocument.create(
            project_id=command.project_id,
            source_id=target.source_id,
            target_run_id=command.target_run_id,
            baseline_run_id=command.baseline_run_id,
            title=f"Technical Source Overview — {source.api_title}",
            file_name=self._file_name(str(project.key), str(source.name), command.target_run_id),
            content=content,
            operation_count=len(operations),
            schema_count=len(schemas),
            breaking_change_count=comparison.breaking_total if comparison is not None else 0,
        )
        await self._repository.add(document)
        return DocumentDetailDto.from_domain(document)

    async def list_documents(self, project_id: str) -> list[DocumentSummaryDto]:
        project = await self._project_repository.get(ProjectId.from_string(project_id))
        if project is None:
            raise DocumentProjectNotFoundError(f"Project {project_id} was not found.")
        documents = await self._repository.list_by_project(project_id)
        return [DocumentSummaryDto.from_domain(document) for document in documents]

    async def get_document(self, document_id: str) -> DocumentDetailDto:
        document = await self._repository.get(DocumentId.from_string(document_id))
        if document is None:
            raise DocumentNotFoundError(f"Document {document_id} was not found.")
        return DocumentDetailDto.from_domain(document)

    @staticmethod
    def _file_name(project_key: str, source_name: str, target_run_id: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", source_name.casefold()).strip("-")
        source_slug = slug or "source"
        return (
            f"{project_key.casefold()}-{source_slug}-technical-source-overview-"
            f"{target_run_id[:8]}.md"
        )
