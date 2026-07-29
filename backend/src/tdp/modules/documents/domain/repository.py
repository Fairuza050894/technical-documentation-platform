from typing import Protocol

from tdp.modules.documents.domain.model import DocumentId, GeneratedDocument


class DocumentRepository(Protocol):
    async def add(self, document: GeneratedDocument) -> None: ...

    async def get(self, document_id: DocumentId) -> GeneratedDocument | None: ...

    async def list_by_project(self, project_id: str) -> list[GeneratedDocument]: ...
