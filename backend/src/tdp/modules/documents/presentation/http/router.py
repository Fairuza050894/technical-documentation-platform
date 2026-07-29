from dataclasses import asdict
from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from tdp.modules.documents.application.commands import GenerateTechnicalSourceOverviewCommand
from tdp.modules.documents.application.dto import DocumentDetailDto, DocumentSummaryDto
from tdp.modules.documents.application.service import DocumentApplicationService

router = APIRouter(tags=["documents"])


class GenerateTechnicalSourceOverviewRequest(BaseModel):
    target_run_id: str
    baseline_run_id: str | None = None


class DocumentSummaryResponse(BaseModel):
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
    def from_dto(cls, document: DocumentSummaryDto) -> "DocumentSummaryResponse":
        return cls.model_validate(asdict(document))


class DocumentDetailResponse(DocumentSummaryResponse):
    content: str

    @classmethod
    def from_dto(cls, document: DocumentDetailDto) -> "DocumentDetailResponse":
        return cls.model_validate(asdict(document))


class DocumentCollectionResponse(BaseModel):
    items: list[DocumentSummaryResponse]
    total: int


def get_document_service(request: Request) -> DocumentApplicationService:
    return cast(DocumentApplicationService, request.app.state.document_service)


DocumentServiceDependency = Annotated[DocumentApplicationService, Depends(get_document_service)]


@router.post(
    "/projects/{project_id}/documents/technical-source-overview",
    response_model=DocumentDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_technical_source_overview(
    project_id: str,
    payload: GenerateTechnicalSourceOverviewRequest,
    service: DocumentServiceDependency,
) -> DocumentDetailResponse:
    document = await service.generate(
        GenerateTechnicalSourceOverviewCommand(
            project_id=project_id,
            target_run_id=payload.target_run_id,
            baseline_run_id=payload.baseline_run_id,
        )
    )
    return DocumentDetailResponse.from_dto(document)


@router.get(
    "/projects/{project_id}/documents",
    response_model=DocumentCollectionResponse,
)
async def list_documents(
    project_id: str,
    service: DocumentServiceDependency,
) -> DocumentCollectionResponse:
    documents = await service.list_documents(project_id)
    items = [DocumentSummaryResponse.from_dto(document) for document in documents]
    return DocumentCollectionResponse(items=items, total=len(items))


@router.get("/documents/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: str,
    service: DocumentServiceDependency,
) -> DocumentDetailResponse:
    return DocumentDetailResponse.from_dto(await service.get_document(document_id))


@router.get("/documents/{document_id}/download", response_class=PlainTextResponse)
async def download_document(
    document_id: str,
    service: DocumentServiceDependency,
) -> PlainTextResponse:
    document = await service.get_document(document_id)
    return PlainTextResponse(
        content=document.content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{document.file_name}"',
            "X-Document-Checksum": document.checksum,
        },
    )
