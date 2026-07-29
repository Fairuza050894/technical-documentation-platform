from dataclasses import asdict
from typing import Annotated, Self, cast

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from tdp.modules.documents.application.commands import (
    DocumentWorkflowCommand,
    GenerateTechnicalSourceOverviewCommand,
)
from tdp.modules.documents.application.dto import (
    DocumentDetailDto,
    DocumentSummaryDto,
    WorkflowEventDto,
)
from tdp.modules.documents.application.service import DocumentApplicationService

router = APIRouter(tags=["documents"])


class GenerateTechnicalSourceOverviewRequest(BaseModel):
    target_run_id: str
    baseline_run_id: str | None = None
    revision_reason: str = Field(default="", max_length=500)
    actor: str = Field(default="System Generator", min_length=2, max_length=80)


class DocumentWorkflowRequest(BaseModel):
    actor: str = Field(min_length=2, max_length=80)
    comment: str = Field(default="", max_length=1000)


class DocumentSummaryResponse(BaseModel):
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
    def from_dto(cls, document: DocumentSummaryDto) -> Self:
        return cls.model_validate(asdict(document))


class DocumentDetailResponse(DocumentSummaryResponse):
    content: str
    reused_existing_version: bool


class DocumentCollectionResponse(BaseModel):
    items: list[DocumentSummaryResponse]
    total: int


class WorkflowEventResponse(BaseModel):
    id: str
    version_id: str
    actor: str
    action: str
    previous_status: str | None
    new_status: str
    comment: str
    created_at: str

    @classmethod
    def from_dto(cls, event: WorkflowEventDto) -> "WorkflowEventResponse":
        return cls.model_validate(asdict(event))


class WorkflowEventCollectionResponse(BaseModel):
    items: list[WorkflowEventResponse]
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
            revision_reason=payload.revision_reason,
            actor=payload.actor,
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


@router.get(
    "/documents/{document_id}/versions",
    response_model=DocumentCollectionResponse,
)
async def list_document_versions(
    document_id: str,
    service: DocumentServiceDependency,
) -> DocumentCollectionResponse:
    versions = await service.list_versions(document_id)
    items = [DocumentSummaryResponse.from_dto(version) for version in versions]
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
    return _download_response(await service.get_document(document_id))


@router.get("/document-versions/{version_id}", response_model=DocumentDetailResponse)
async def get_document_version(
    version_id: str,
    service: DocumentServiceDependency,
) -> DocumentDetailResponse:
    return DocumentDetailResponse.from_dto(await service.get_version(version_id))


@router.get("/document-versions/{version_id}/download", response_class=PlainTextResponse)
async def download_document_version(
    version_id: str,
    service: DocumentServiceDependency,
) -> PlainTextResponse:
    return _download_response(await service.get_version(version_id))


@router.post(
    "/document-versions/{version_id}/submit-review",
    response_model=DocumentDetailResponse,
)
async def submit_document_version_for_review(
    version_id: str,
    payload: DocumentWorkflowRequest,
    service: DocumentServiceDependency,
) -> DocumentDetailResponse:
    document = await service.submit_for_review(_workflow_command(version_id, payload))
    return DocumentDetailResponse.from_dto(document)


@router.post(
    "/document-versions/{version_id}/request-changes",
    response_model=DocumentDetailResponse,
)
async def request_document_version_changes(
    version_id: str,
    payload: DocumentWorkflowRequest,
    service: DocumentServiceDependency,
) -> DocumentDetailResponse:
    document = await service.request_changes(_workflow_command(version_id, payload))
    return DocumentDetailResponse.from_dto(document)


@router.post(
    "/document-versions/{version_id}/approve",
    response_model=DocumentDetailResponse,
)
async def approve_document_version(
    version_id: str,
    payload: DocumentWorkflowRequest,
    service: DocumentServiceDependency,
) -> DocumentDetailResponse:
    document = await service.approve(_workflow_command(version_id, payload))
    return DocumentDetailResponse.from_dto(document)


@router.post(
    "/document-versions/{version_id}/supersede",
    response_model=DocumentDetailResponse,
)
async def supersede_document_version(
    version_id: str,
    payload: DocumentWorkflowRequest,
    service: DocumentServiceDependency,
) -> DocumentDetailResponse:
    document = await service.supersede(_workflow_command(version_id, payload))
    return DocumentDetailResponse.from_dto(document)


@router.get(
    "/document-versions/{version_id}/workflow-events",
    response_model=WorkflowEventCollectionResponse,
)
async def list_document_version_workflow_events(
    version_id: str,
    service: DocumentServiceDependency,
) -> WorkflowEventCollectionResponse:
    events = await service.list_workflow_events(version_id)
    items = [WorkflowEventResponse.from_dto(event) for event in events]
    return WorkflowEventCollectionResponse(items=items, total=len(items))


def _workflow_command(
    version_id: str,
    payload: DocumentWorkflowRequest,
) -> DocumentWorkflowCommand:
    return DocumentWorkflowCommand(
        version_id=version_id,
        actor=payload.actor,
        comment=payload.comment,
    )


def _download_response(document: DocumentDetailDto) -> PlainTextResponse:
    return PlainTextResponse(
        content=document.content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{document.file_name}"',
            "X-Document-Checksum": document.checksum,
            "X-Document-Version": document.version,
            "X-Document-Status": document.status,
        },
    )
