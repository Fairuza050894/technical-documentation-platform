from collections.abc import Mapping
from dataclasses import asdict
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from tdp.modules.requirements.application.commands import (
    CreateRequirementCommand,
    CreateTraceLinkCommand,
    RetireRequirementCommand,
    ReviseRequirementCommand,
)
from tdp.modules.requirements.application.dto import RequirementDto, TraceabilityCoverageDto
from tdp.modules.requirements.application.service import RequirementApplicationService
from tdp.modules.requirements.domain.errors import (
    InvalidAcceptanceCriterionError,
    InvalidRequirementActorError,
    InvalidRequirementIdError,
    InvalidRequirementKeyError,
    InvalidRequirementOwnerError,
    InvalidRequirementRevisionIdError,
    InvalidRequirementStatementError,
    InvalidRequirementTitleError,
    InvalidRequirementTypeError,
    InvalidTraceRelationError,
    InvalidTraceTargetError,
    RequirementError,
    RequirementKeyAlreadyExistsError,
    RequirementNotFoundError,
    RequirementProjectArchivedError,
    RequirementProjectNotFoundError,
    RequirementRetiredError,
    RequirementWorkspaceMismatchError,
    TraceLinkAlreadyExistsError,
    TraceTargetNotFoundError,
)
from tdp.presentation.http.dependencies.identity import PrincipalDependency

router = APIRouter(
    prefix="/workspaces/{workspace_id}/projects/{project_id}/requirements",
    tags=["requirements"],
)

RequirementTypeLiteral = Literal["BUSINESS", "SYSTEM", "NON_FUNCTIONAL", "ACCEPTANCE"]
TraceTargetTypeLiteral = Literal["FEATURE", "EVIDENCE", "DOCUMENT"]
TraceRelationLiteral = Literal["IMPLEMENTED_BY", "VERIFIED_BY", "DOCUMENTED_BY"]


class CreateRequirementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=2, max_length=40, pattern=r"^[A-Za-z][A-Za-z0-9-]+$")
    requirement_type: RequirementTypeLiteral
    title: str = Field(min_length=3, max_length=160)
    statement: str = Field(min_length=10, max_length=4000)
    owner: str = Field(min_length=2, max_length=120)
    feature_id: str | None = Field(default=None, max_length=100)
    acceptance_criteria: list[str] = Field(default_factory=list, max_length=50)
    change_reason: str = Field(min_length=3, max_length=500)


class ReviseRequirementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_type: RequirementTypeLiteral
    title: str = Field(min_length=3, max_length=160)
    statement: str = Field(min_length=10, max_length=4000)
    owner: str = Field(min_length=2, max_length=120)
    feature_id: str | None = Field(default=None, max_length=100)
    acceptance_criteria: list[str] = Field(default_factory=list, max_length=50)
    change_reason: str = Field(min_length=3, max_length=500)


class RetireRequirementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    change_reason: str = Field(min_length=3, max_length=500)


class CreateTraceLinkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_type: TraceTargetTypeLiteral
    relation: TraceRelationLiteral
    target_reference: str = Field(min_length=1, max_length=200)


class TraceLinkResponse(BaseModel):
    id: str
    target_type: str
    relation: str
    target_reference: str
    verified: bool
    created_by: str
    created_at: str


class RequirementResponse(BaseModel):
    requirement_id: str
    revision_id: str
    project_id: str
    key: str
    revision: int
    requirement_type: str
    status: str
    title: str
    statement: str
    owner: str
    feature_id: str | None
    acceptance_criteria: list[str]
    changed_by: str
    change_reason: str
    created_at: str
    trace_links: list[TraceLinkResponse]

    @classmethod
    def from_dto(cls, requirement: RequirementDto) -> "RequirementResponse":
        payload = asdict(requirement)
        payload["acceptance_criteria"] = list(requirement.acceptance_criteria)
        payload["trace_links"] = [asdict(item) for item in requirement.trace_links]
        return cls.model_validate(payload)


class RequirementCollectionResponse(BaseModel):
    items: list[RequirementResponse]
    total: int


class TraceabilityCoverageResponse(BaseModel):
    total_requirements: int
    linked_to_feature: int
    linked_to_evidence: int
    linked_to_document: int
    fully_traced: int
    coverage_percent: int

    @classmethod
    def from_dto(cls, coverage: TraceabilityCoverageDto) -> "TraceabilityCoverageResponse":
        return cls(
            total_requirements=coverage.total_requirements,
            linked_to_feature=coverage.linked_to_feature,
            linked_to_evidence=coverage.linked_to_evidence,
            linked_to_document=coverage.linked_to_document,
            fully_traced=coverage.fully_traced,
            coverage_percent=coverage.coverage_percent,
        )


def get_requirement_service(request: Request) -> RequirementApplicationService:
    return cast(RequirementApplicationService, request.app.state.requirement_service)


RequirementServiceDependency = Annotated[
    RequirementApplicationService,
    Depends(get_requirement_service),
]


@router.post("", response_model=RequirementResponse, status_code=status.HTTP_201_CREATED)
async def create_requirement(
    workspace_id: str,
    project_id: str,
    payload: CreateRequirementRequest,
    principal: PrincipalDependency,
    service: RequirementServiceDependency,
) -> RequirementResponse:
    requirement = await service.create(
        CreateRequirementCommand(
            workspace_id=workspace_id,
            project_id=project_id,
            key=payload.key,
            requirement_type=payload.requirement_type,
            title=payload.title,
            statement=payload.statement,
            owner=payload.owner,
            feature_id=payload.feature_id,
            acceptance_criteria=tuple(payload.acceptance_criteria),
            actor=principal.audit_actor,
            change_reason=payload.change_reason,
        )
    )
    return RequirementResponse.from_dto(requirement)


@router.get("", response_model=RequirementCollectionResponse)
async def list_requirements(
    workspace_id: str,
    project_id: str,
    service: RequirementServiceDependency,
) -> RequirementCollectionResponse:
    requirements = await service.list_requirements(workspace_id, project_id)
    items = [RequirementResponse.from_dto(item) for item in requirements]
    return RequirementCollectionResponse(items=items, total=len(items))


@router.get("/traceability/coverage", response_model=TraceabilityCoverageResponse)
async def get_traceability_coverage(
    workspace_id: str,
    project_id: str,
    service: RequirementServiceDependency,
) -> TraceabilityCoverageResponse:
    return TraceabilityCoverageResponse.from_dto(await service.coverage(workspace_id, project_id))


@router.get("/{requirement_id}", response_model=RequirementResponse)
async def get_requirement(
    workspace_id: str,
    project_id: str,
    requirement_id: str,
    service: RequirementServiceDependency,
) -> RequirementResponse:
    return RequirementResponse.from_dto(await service.get(workspace_id, project_id, requirement_id))


@router.get("/{requirement_id}/revisions", response_model=RequirementCollectionResponse)
async def list_requirement_revisions(
    workspace_id: str,
    project_id: str,
    requirement_id: str,
    service: RequirementServiceDependency,
) -> RequirementCollectionResponse:
    revisions = await service.list_revisions(workspace_id, project_id, requirement_id)
    items = [RequirementResponse.from_dto(item) for item in revisions]
    return RequirementCollectionResponse(items=items, total=len(items))


@router.post("/{requirement_id}/revisions", response_model=RequirementResponse)
async def revise_requirement(
    workspace_id: str,
    project_id: str,
    requirement_id: str,
    payload: ReviseRequirementRequest,
    principal: PrincipalDependency,
    service: RequirementServiceDependency,
) -> RequirementResponse:
    requirement = await service.revise(
        ReviseRequirementCommand(
            workspace_id=workspace_id,
            project_id=project_id,
            requirement_id=requirement_id,
            requirement_type=payload.requirement_type,
            title=payload.title,
            statement=payload.statement,
            owner=payload.owner,
            feature_id=payload.feature_id,
            acceptance_criteria=tuple(payload.acceptance_criteria),
            actor=principal.audit_actor,
            change_reason=payload.change_reason,
        )
    )
    return RequirementResponse.from_dto(requirement)


@router.post("/{requirement_id}/retire", response_model=RequirementResponse)
async def retire_requirement(
    workspace_id: str,
    project_id: str,
    requirement_id: str,
    payload: RetireRequirementRequest,
    principal: PrincipalDependency,
    service: RequirementServiceDependency,
) -> RequirementResponse:
    requirement = await service.retire(
        RetireRequirementCommand(
            workspace_id=workspace_id,
            project_id=project_id,
            requirement_id=requirement_id,
            actor=principal.audit_actor,
            change_reason=payload.change_reason,
        )
    )
    return RequirementResponse.from_dto(requirement)


@router.post("/{requirement_id}/trace-links", response_model=RequirementResponse)
async def add_requirement_trace_link(
    workspace_id: str,
    project_id: str,
    requirement_id: str,
    payload: CreateTraceLinkRequest,
    principal: PrincipalDependency,
    service: RequirementServiceDependency,
) -> RequirementResponse:
    requirement = await service.add_trace_link(
        CreateTraceLinkCommand(
            workspace_id=workspace_id,
            project_id=project_id,
            requirement_id=requirement_id,
            target_type=payload.target_type,
            relation=payload.relation,
            target_reference=payload.target_reference,
            actor=principal.audit_actor,
        )
    )
    return RequirementResponse.from_dto(requirement)


_REQUIREMENT_ERROR_STATUS: Mapping[type[RequirementError], int] = {
    InvalidRequirementIdError: 422,
    InvalidRequirementRevisionIdError: 422,
    InvalidRequirementKeyError: 422,
    InvalidRequirementTitleError: 422,
    InvalidRequirementStatementError: 422,
    InvalidRequirementOwnerError: 422,
    InvalidRequirementActorError: 422,
    InvalidAcceptanceCriterionError: 422,
    InvalidRequirementTypeError: 422,
    InvalidTraceTargetError: 422,
    InvalidTraceRelationError: 422,
    RequirementKeyAlreadyExistsError: 409,
    RequirementNotFoundError: 404,
    RequirementRetiredError: 409,
    RequirementProjectNotFoundError: 404,
    RequirementWorkspaceMismatchError: 404,
    RequirementProjectArchivedError: 409,
    TraceTargetNotFoundError: 404,
    TraceLinkAlreadyExistsError: 409,
}


async def requirement_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequirementError):
        raise exc
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=_REQUIREMENT_ERROR_STATUS.get(type(exc), 400),
        content={
            "error": {
                "code": exc.code,
                "message": str(exc),
                "requestId": request_id,
            }
        },
    )
