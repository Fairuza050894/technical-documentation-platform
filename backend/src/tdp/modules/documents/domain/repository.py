from typing import Protocol

from tdp.modules.documents.domain.model import (
    DocumentId,
    DocumentSeries,
    DocumentType,
    DocumentVersion,
    DocumentVersionId,
    DocumentWorkflowEvent,
)


class DocumentRepository(Protocol):
    async def get_series(self, document_id: DocumentId) -> DocumentSeries | None: ...

    async def get_series_by_project_type(
        self,
        project_id: str,
        document_type: DocumentType,
    ) -> DocumentSeries | None: ...

    async def add_version(
        self,
        series: DocumentSeries,
        version: DocumentVersion,
        event: DocumentWorkflowEvent,
    ) -> None: ...

    async def get_version(self, version_id: DocumentVersionId) -> DocumentVersion | None: ...

    async def find_version_by_checksum(
        self,
        document_id: DocumentId,
        checksum: str,
    ) -> DocumentVersion | None: ...

    async def get_current_approved_version(
        self,
        document_id: DocumentId,
    ) -> DocumentVersion | None: ...

    async def list_versions_by_project(self, project_id: str) -> list[DocumentVersion]: ...

    async def list_versions(self, document_id: DocumentId) -> list[DocumentVersion]: ...

    async def apply_workflow_transition(
        self,
        series: DocumentSeries,
        version: DocumentVersion,
        event: DocumentWorkflowEvent,
        *,
        superseded_version: DocumentVersion | None = None,
        superseded_event: DocumentWorkflowEvent | None = None,
    ) -> None: ...

    async def list_workflow_events(
        self,
        version_id: DocumentVersionId,
    ) -> list[DocumentWorkflowEvent]: ...
