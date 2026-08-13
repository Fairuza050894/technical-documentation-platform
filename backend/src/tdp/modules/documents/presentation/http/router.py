from dataclasses import asdict
from typing import Annotated, Self, cast

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field

from tdp.modules.documents.application.commands import (
    CompareDocumentVersionsCommand,
    DocumentWorkflowCommand,
    GenerateEnterpriseDocumentCommand,
    GenerateTechnicalSourceOverviewCommand,
)
from tdp.modules.documents.application.dto import (
    DocumentDetailDto,
    DocumentSummaryDto,
    DocumentVersionComparisonDto,
    WorkflowEventDto,
)
from tdp.modules.documents.application.enterprise_generation_service import (
    EnterpriseDocumentGenerationService,
)
from tdp.modules.documents.application.governance_dto import (
    DocumentTypeDefinitionDto,
    DocumentTypeRegistryDto,
    ProjectDocumentationChecklistDto,
    ProjectDocumentationChecklistItemDto,
)
from tdp.modules.documents.application.governance_service import (
    DocumentGovernanceApplicationService,
)
from tdp.modules.documents.application.service import DocumentApplicationService
from tdp.modules.documents.domain.errors import EnterpriseDocumentGenerationBlockedError
from tdp.presentation.http.dependencies.identity import PrincipalDependency

router = APIRouter(tags=["documents"])


class GenerateTechnicalSourceOverviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_run_id: str
    baseline_run_id: str | None = None
    revision_reason: str = Field(default="", max_length=500)


class GenerateEnterpriseDocumentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_reason: str = Field(default="", max_length=500)


class DocumentWorkflowRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comment: str = Field(default="", max_length=1000)


class CompareDocumentVersionsRequest(BaseModel):
    baseline_version_id: str
    target_version_id: str


class DocumentProvenanceResponse(BaseModel):
    kind: str
    reference: str
    evidence_kind: str | None
    checksum: str | None


class DocumentSummaryResponse(BaseModel):
    id: str
    document_id: str
    project_id: str
    source_id: str | None
    target_run_id: str | None
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
    provenance: list[DocumentProvenanceResponse]

    @classmethod
    def from_dto(cls, document: DocumentSummaryDto) -> Self:
        return cls.model_validate(asdict(document))


class DocumentDetailResponse(DocumentSummaryResponse):
    content: str
    reused_existing_version: bool


class DocumentCollectionResponse(BaseModel):
    items: list[DocumentSummaryResponse]
    total: int


class DocumentTypeDefinitionResponse(BaseModel):
    document_type: str
    display_name: str
    description: str
    automation_profile: str
    order: int

    @classmethod
    def from_dto(cls, item: DocumentTypeDefinitionDto) -> "DocumentTypeDefinitionResponse":
        return cls.model_validate(asdict(item))


class DocumentTypeRegistryResponse(BaseModel):
    schema_version: str
    items: list[DocumentTypeDefinitionResponse]
    total: int

    @classmethod
    def from_dto(cls, registry: DocumentTypeRegistryDto) -> "DocumentTypeRegistryResponse":
        return cls(
            schema_version=registry.schema_version,
            items=[DocumentTypeDefinitionResponse.from_dto(item) for item in registry.items],
            total=registry.total,
        )


class ProjectDocumentationChecklistItemResponse(BaseModel):
    document_type: str
    display_name: str
    automation_profile: str
    requirement: str
    availability: str
    latest_document_id: str | None
    latest_version_id: str | None
    latest_version: str | None
    latest_status: str | None

    @classmethod
    def from_dto(
        cls,
        item: ProjectDocumentationChecklistItemDto,
    ) -> "ProjectDocumentationChecklistItemResponse":
        return cls.model_validate(asdict(item))


class ProjectDocumentationChecklistResponse(BaseModel):
    project_id: str
    policy_key: str
    registry_schema_version: str
    items: list[ProjectDocumentationChecklistItemResponse]
    total: int
    required_total: int
    supplementary_total: int
    available_total: int
    missing_required_total: int

    @classmethod
    def from_dto(
        cls,
        checklist: ProjectDocumentationChecklistDto,
    ) -> "ProjectDocumentationChecklistResponse":
        return cls(
            project_id=checklist.project_id,
            policy_key=checklist.policy_key,
            registry_schema_version=checklist.registry_schema_version,
            items=[
                ProjectDocumentationChecklistItemResponse.from_dto(item) for item in checklist.items
            ],
            total=checklist.total,
            required_total=checklist.required_total,
            supplementary_total=checklist.supplementary_total,
            available_total=checklist.available_total,
            missing_required_total=checklist.missing_required_total,
        )


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


class DocumentSectionChangeResponse(BaseModel):
    section_key: str
    section_title: str
    kind: str
    before_checksum: str
    after_checksum: str
    before_excerpt: str
    after_excerpt: str


class DocumentVersionComparisonResponse(BaseModel):
    baseline_version_id: str
    target_version_id: str
    document_id: str
    total: int
    added_total: int
    modified_total: int
    removed_total: int
    changes: list[DocumentSectionChangeResponse]

    @classmethod
    def from_dto(
        cls, comparison: DocumentVersionComparisonDto
    ) -> "DocumentVersionComparisonResponse":
        return cls.model_validate(asdict(comparison))


def get_document_service(request: Request) -> DocumentApplicationService:
    return cast(DocumentApplicationService, request.app.state.document_service)


def get_enterprise_generation_service(
    request: Request,
) -> EnterpriseDocumentGenerationService:
    return cast(
        EnterpriseDocumentGenerationService,
        request.app.state.enterprise_generation_service,
    )


def get_document_governance_service(request: Request) -> DocumentGovernanceApplicationService:
    return cast(
        DocumentGovernanceApplicationService,
        request.app.state.document_governance_service,
    )


DocumentServiceDependency = Annotated[DocumentApplicationService, Depends(get_document_service)]
EnterpriseGenerationServiceDependency = Annotated[
    EnterpriseDocumentGenerationService,
    Depends(get_enterprise_generation_service),
]
DocumentGovernanceServiceDependency = Annotated[
    DocumentGovernanceApplicationService,
    Depends(get_document_governance_service),
]


@router.get("/document-types", response_model=DocumentTypeRegistryResponse)
async def list_document_types(
    service: DocumentGovernanceServiceDependency,
) -> DocumentTypeRegistryResponse:
    return DocumentTypeRegistryResponse.from_dto(await service.list_document_types())


@router.get(
    "/projects/{project_id}/documentation-checklist",
    response_model=ProjectDocumentationChecklistResponse,
)
async def get_project_documentation_checklist(
    project_id: str,
    service: DocumentGovernanceServiceDependency,
) -> ProjectDocumentationChecklistResponse:
    checklist = await service.project_documentation_checklist(project_id)
    return ProjectDocumentationChecklistResponse.from_dto(checklist)


@router.post(
    "/projects/{project_id}/documents/{document_type}/generate",
    response_model=DocumentDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_enterprise_document(
    project_id: str,
    document_type: str,
    payload: GenerateEnterpriseDocumentRequest,
    service: EnterpriseGenerationServiceDependency,
    principal: PrincipalDependency,
) -> DocumentDetailResponse:
    document = await service.generate(
        GenerateEnterpriseDocumentCommand(
            project_id=project_id,
            document_type=document_type,
            principal=principal,
            revision_reason=payload.revision_reason,
        )
    )
    return DocumentDetailResponse.from_dto(document)


@router.post(
    "/projects/{project_id}/documents/technical-source-overview",
    response_model=DocumentDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_technical_source_overview(
    project_id: str,
    payload: GenerateTechnicalSourceOverviewRequest,
    service: DocumentServiceDependency,
    principal: PrincipalDependency,
) -> DocumentDetailResponse:
    document = await service.generate(
        GenerateTechnicalSourceOverviewCommand(
            project_id=project_id,
            target_run_id=payload.target_run_id,
            principal=principal,
            baseline_run_id=payload.baseline_run_id,
            revision_reason=payload.revision_reason,
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
    principal: PrincipalDependency,
) -> DocumentDetailResponse:
    document = await service.submit_for_review(_workflow_command(version_id, payload, principal))
    return DocumentDetailResponse.from_dto(document)


@router.post(
    "/document-versions/{version_id}/request-changes",
    response_model=DocumentDetailResponse,
)
async def request_document_version_changes(
    version_id: str,
    payload: DocumentWorkflowRequest,
    service: DocumentServiceDependency,
    principal: PrincipalDependency,
) -> DocumentDetailResponse:
    document = await service.request_changes(_workflow_command(version_id, payload, principal))
    return DocumentDetailResponse.from_dto(document)


@router.post(
    "/document-versions/{version_id}/approve",
    response_model=DocumentDetailResponse,
)
async def approve_document_version(
    version_id: str,
    payload: DocumentWorkflowRequest,
    service: DocumentServiceDependency,
    principal: PrincipalDependency,
) -> DocumentDetailResponse:
    document = await service.approve(_workflow_command(version_id, payload, principal))
    return DocumentDetailResponse.from_dto(document)


@router.post(
    "/document-versions/{version_id}/supersede",
    response_model=DocumentDetailResponse,
)
async def supersede_document_version(
    version_id: str,
    payload: DocumentWorkflowRequest,
    service: DocumentServiceDependency,
    principal: PrincipalDependency,
) -> DocumentDetailResponse:
    document = await service.supersede(_workflow_command(version_id, payload, principal))
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


@router.post(
    "/document-version-comparisons",
    response_model=DocumentVersionComparisonResponse,
)
async def compare_document_versions(
    payload: CompareDocumentVersionsRequest,
    service: DocumentServiceDependency,
) -> DocumentVersionComparisonResponse:
    comparison = await service.compare_versions(
        CompareDocumentVersionsCommand(
            baseline_version_id=payload.baseline_version_id,
            target_version_id=payload.target_version_id,
        )
    )
    return DocumentVersionComparisonResponse.from_dto(comparison)


async def enterprise_generation_blocked_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(exc, EnterpriseDocumentGenerationBlockedError):
        raise exc
    request_id = getattr(request.state, "request_id", "unknown")
    details = [
        {
            "rule_code": item.rule_code,
            "severity": item.severity,
            "message": item.message,
            "missing_input": item.missing_input,
            "remediation": item.remediation,
            "supporting_references": list(item.supporting_references),
        }
        for item in exc.findings
    ]
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": {
                "code": exc.code,
                "message": str(exc),
                "details": details,
                "requestId": request_id,
                "documentType": exc.document_type,
                "readinessState": exc.readiness_state,
                "policyVersion": exc.policy_version,
            }
        },
        headers={"X-Request-ID": request_id},
    )


def _workflow_command(
    version_id: str,
    payload: DocumentWorkflowRequest,
    principal: PrincipalDependency,
) -> DocumentWorkflowCommand:
    return DocumentWorkflowCommand(
        version_id=version_id,
        principal=principal,
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
