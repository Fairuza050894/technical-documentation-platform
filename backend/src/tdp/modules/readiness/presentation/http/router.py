from collections.abc import Mapping
from dataclasses import asdict
from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from tdp.modules.readiness.application.dto import (
    DocumentReadinessDto,
    ProjectReadinessDto,
    ReadinessFindingDto,
)
from tdp.modules.readiness.application.service import ReadinessApplicationService
from tdp.modules.readiness.domain.errors import (
    InvalidReadinessDocumentTypeError,
    ReadinessError,
    ReadinessProjectNotFoundError,
)

router = APIRouter(tags=["readiness"])


class ReadinessFindingResponse(BaseModel):
    rule_code: str
    document_type: str
    severity: str
    message: str
    missing_input: str
    remediation: str
    supporting_references: list[str]

    @classmethod
    def from_dto(cls, item: ReadinessFindingDto) -> "ReadinessFindingResponse":
        return cls.model_validate(asdict(item))


class DocumentReadinessResponse(BaseModel):
    project_id: str
    policy_version: str
    document_type: str
    display_name: str
    automation_profile: str
    requirement: str
    availability: str
    latest_status: str | None
    readiness_state: str
    eligible: bool
    findings: list[ReadinessFindingResponse]
    evidence_count: int
    observed_claim_count: int
    inferred_claim_count: int
    unverified_claim_count: int

    @classmethod
    def from_dto(cls, item: DocumentReadinessDto) -> "DocumentReadinessResponse":
        payload = asdict(item)
        payload["findings"] = [
            ReadinessFindingResponse.from_dto(finding) for finding in item.findings
        ]
        return cls.model_validate(payload)


class ProjectReadinessResponse(BaseModel):
    project_id: str
    project_status: str
    policy_version: str
    items: list[DocumentReadinessResponse]
    total: int
    ready_total: int
    partially_ready_total: int
    not_ready_total: int
    eligible_total: int
    required_total: int
    required_not_ready_total: int

    @classmethod
    def from_dto(cls, summary: ProjectReadinessDto) -> "ProjectReadinessResponse":
        return cls(
            project_id=summary.project_id,
            project_status=summary.project_status,
            policy_version=summary.policy_version,
            items=[DocumentReadinessResponse.from_dto(item) for item in summary.items],
            total=summary.total,
            ready_total=summary.ready_total,
            partially_ready_total=summary.partially_ready_total,
            not_ready_total=summary.not_ready_total,
            eligible_total=summary.eligible_total,
            required_total=summary.required_total,
            required_not_ready_total=summary.required_not_ready_total,
        )


def get_readiness_service(request: Request) -> ReadinessApplicationService:
    return cast(ReadinessApplicationService, request.app.state.readiness_service)


ReadinessServiceDependency = Annotated[
    ReadinessApplicationService,
    Depends(get_readiness_service),
]


@router.get(
    "/projects/{project_id}/readiness",
    response_model=ProjectReadinessResponse,
)
async def get_project_readiness(
    project_id: str,
    service: ReadinessServiceDependency,
) -> ProjectReadinessResponse:
    return ProjectReadinessResponse.from_dto(await service.project_readiness(project_id))


@router.get(
    "/projects/{project_id}/readiness/{document_type}",
    response_model=DocumentReadinessResponse,
)
async def get_document_readiness(
    project_id: str,
    document_type: str,
    service: ReadinessServiceDependency,
) -> DocumentReadinessResponse:
    return DocumentReadinessResponse.from_dto(
        await service.document_readiness(project_id, document_type)
    )


_READINESS_ERROR_STATUS: Mapping[type[ReadinessError], int] = {
    InvalidReadinessDocumentTypeError: 422,
    ReadinessProjectNotFoundError: 404,
}


async def readiness_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ReadinessError):
        raise exc
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=_READINESS_ERROR_STATUS.get(type(exc), 400),
        content={
            "error": {
                "code": exc.code,
                "message": str(exc),
                "details": [],
                "requestId": request_id,
            }
        },
        headers={"X-Request-ID": request_id},
    )
