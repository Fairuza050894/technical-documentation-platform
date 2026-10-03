from collections.abc import Mapping
from dataclasses import asdict
from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from tdp.identity.provider import IdentityProvider
from tdp.modules.requirements.application.service import RequirementApplicationService
from tdp.modules.requirements.domain.errors import (
    InvalidRequirementAcceptanceCriteriaError,
    InvalidRequirementIdError,
    InvalidRequirementKeyError,
    InvalidRequirementRationaleError,
    InvalidRequirementStatementError,
    InvalidRequirementStatusTransitionError,
    InvalidRequirementTitleError,
    InvalidRequirementTypeError,
    InvalidTraceabilityTargetError,
    RequirementError,
    RequirementFeatureNotFoundError,
    RequirementKeyAlreadyExistsError,
    RequirementNotFoundError,
    RequirementProjectArchivedError,
    RequirementProjectNotFoundError,
    RequirementWorkspaceMismatchError,
    TraceabilityLinkAlreadyExistsError,
    TraceabilityTargetNotFoundError,
)
from tdp.modules.requirements.domain.model import (
    Requirement,
    RequirementRevision,
    TraceabilityLink,
)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/projects/{project_id}/requirements",
    tags=["requirements"],
)


class RequirementRequest(BaseModel):
    key: str = Field(min_length=2, max_length=40, pattern=r"^[A-Za-z][A-Za-z0-9-]+$")
    requirement_type: str = Field(default="FUNCTIONAL", min_length=3, max_length=30)
    title: str = Field(min_length=3, max_length=160)
    statement: str = Field(min_length=10, max_length=4000)
    acceptance_criteria: list[str] = Field(min_length=1, max_length=25)
    rationale: str = Field(default="", max_length=2000)
    feature_id: str | None = None


class RequirementRevisionRequest(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    statement: str = Field(min_length=10, max_length=4000)
    acceptance_criteria: list[str] = Field(min_length=1, max_length=25)
    rationale: str = Field(default="", max_length=2000)
    feature_id: str | None = None


class RequirementTransitionRequest(BaseModel):
    action: str = Field(min_length=3, max_length=20)


class TraceabilityLinkRequest(BaseModel):
    target_type: str = Field(min_length=3, max_length=20)
    target_id: str = Field(min_length=1, max_length=500)
    relation: str = Field(min_length=3, max_length=30)


class RequirementResponse(BaseModel):
    id: str
    workspace_id: str
    project_id: str
    key: str
    requirement_type: str
    title: str
    statement: str
    acceptance_criteria: list[str]
    rationale: str
    feature_id: str | None
    status: str
    revision: int
    created_by: str
    created_at: str
    updated_at: str

    @classmethod
    def from_domain(cls, requirement: Requirement) -> "RequirementResponse":
        return cls(
            id=str(requirement.id),
            workspace_id=requirement.workspace_id,
            project_id=requirement.project_id,
            key=requirement.key,
            requirement_type=requirement.requirement_type.value,
            title=requirement.title,
            statement=requirement.statement,
            acceptance_criteria=list(requirement.acceptance_criteria),
            rationale=requirement.rationale,
            feature_id=requirement.feature_id,
            status=requirement.status.value,
            revision=requirement.revision,
            created_by=requirement.created_by,
            created_at=requirement.created_at.isoformat(),
            updated_at=requirement.updated_at.isoformat(),
        )


class RequirementCollectionResponse(BaseModel):
    items: list[RequirementResponse]
    total: int


class RequirementRevisionResponse(BaseModel):
    requirement_id: str
    revision: int
    title: str
    statement: str
    acceptance_criteria: list[str]
    rationale: str
    feature_id: str | None
    status: str
    actor: str
    recorded_at: str

    @classmethod
    def from_domain(cls, revision: RequirementRevision) -> "RequirementRevisionResponse":
        return cls(
            requirement_id=str(revision.requirement_id),
            revision=revision.revision,
            title=revision.title,
            statement=revision.statement,
            acceptance_criteria=list(revision.acceptance_criteria),
            rationale=revision.rationale,
            feature_id=revision.feature_id,
            status=revision.status.value,
            actor=revision.actor,
            recorded_at=revision.recorded_at.isoformat(),
        )


class RequirementHistoryResponse(BaseModel):
    items: list[RequirementRevisionResponse]
    total: int


class TraceabilityLinkResponse(BaseModel):
    id: str
    requirement_id: str
    target_type: str
    target_id: str
    relation: str
    created_by: str
    created_at: str

    @classmethod
    def from_domain(cls, link: TraceabilityLink) -> "TraceabilityLinkResponse":
        return cls(
            id=str(link.id),
            requirement_id=str(link.requirement_id),
            target_type=link.target_type.value,
            target_id=link.target_id,
            relation=link.relation.value,
            created_by=link.created_by,
            created_at=link.created_at.isoformat(),
        )


class TraceabilityResponse(BaseModel):
    requirement: RequirementResponse
    links: list[TraceabilityLinkResponse]
    coverage: dict[str, bool]


class ProjectTraceabilityResponse(BaseModel):
    items: list[TraceabilityResponse]
    total: int


def get_service(request: Request) -> RequirementApplicationService:
    return cast(RequirementApplicationService, request.app.state.requirement_service)


ServiceDependency = Annotated[RequirementApplicationService, Depends(get_service)]


def _actor(request: Request) -> str:
    provider = cast(IdentityProvider, request.app.state.identity_provider)
    return provider.current_principal().audit_actor


@router.post("", response_model=RequirementResponse, status_code=status.HTTP_201_CREATED)
async def create_requirement(
    workspace_id: str,
    project_id: str,
    payload: RequirementRequest,
    request: Request,
    service: ServiceDependency,
) -> RequirementResponse:
    requirement = await service.create(
        workspace_id=workspace_id,
        project_id=project_id,
        key=payload.key,
        requirement_type=payload.requirement_type,
        title=payload.title,
        statement=payload.statement,
        acceptance_criteria=tuple(payload.acceptance_criteria),
        rationale=payload.rationale,
        feature_id=payload.feature_id,
        actor=_actor(request),
    )
    return RequirementResponse.from_domain(requirement)


@router.get("", response_model=RequirementCollectionResponse)
async def list_requirements(
    workspace_id: str,
    project_id: str,
    service: ServiceDependency,
) -> RequirementCollectionResponse:
    requirements = await service.list_requirements(workspace_id, project_id)
    items = [RequirementResponse.from_domain(item) for item in requirements]
    return RequirementCollectionResponse(items=items, total=len(items))


@router.get("/traceability", response_model=ProjectTraceabilityResponse)
async def project_traceability(
    workspace_id: str,
    project_id: str,
    service: ServiceDependency,
) -> ProjectTraceabilityResponse:
    rows = await service.project_traceability(workspace_id, project_id)
    items = [_traceability_response(requirement, links) for requirement, links in rows]
    return ProjectTraceabilityResponse(items=items, total=len(items))


@router.get("/{requirement_id}", response_model=RequirementResponse)
async def get_requirement(
    workspace_id: str,
    project_id: str,
    requirement_id: str,
    service: ServiceDependency,
) -> RequirementResponse:
    return RequirementResponse.from_domain(
        await service.get(workspace_id, project_id, requirement_id)
    )


@router.put("/{requirement_id}", response_model=RequirementResponse)
async def revise_requirement(
    workspace_id: str,
    project_id: str,
    requirement_id: str,
    payload: RequirementRevisionRequest,
    request: Request,
    service: ServiceDependency,
) -> RequirementResponse:
    requirement = await service.revise(
        workspace_id=workspace_id,
        project_id=project_id,
        requirement_id=requirement_id,
        title=payload.title,
        statement=payload.statement,
        acceptance_criteria=tuple(payload.acceptance_criteria),
        rationale=payload.rationale,
        feature_id=payload.feature_id,
        actor=_actor(request),
    )
    return RequirementResponse.from_domain(requirement)


@router.post("/{requirement_id}/transition", response_model=RequirementResponse)
async def transition_requirement(
    workspace_id: str,
    project_id: str,
    requirement_id: str,
    payload: RequirementTransitionRequest,
    request: Request,
    service: ServiceDependency,
) -> RequirementResponse:
    requirement = await service.transition(
        workspace_id=workspace_id,
        project_id=project_id,
        requirement_id=requirement_id,
        action=payload.action,
        actor=_actor(request),
    )
    return RequirementResponse.from_domain(requirement)


@router.get("/{requirement_id}/history", response_model=RequirementHistoryResponse)
async def requirement_history(
    workspace_id: str,
    project_id: str,
    requirement_id: str,
    service: ServiceDependency,
) -> RequirementHistoryResponse:
    revisions = await service.history(workspace_id, project_id, requirement_id)
    items = [RequirementRevisionResponse.from_domain(item) for item in revisions]
    return RequirementHistoryResponse(items=items, total=len(items))


@router.post(
    "/{requirement_id}/traceability",
    response_model=TraceabilityLinkResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_traceability_link(
    workspace_id: str,
    project_id: str,
    requirement_id: str,
    payload: TraceabilityLinkRequest,
    request: Request,
    service: ServiceDependency,
) -> TraceabilityLinkResponse:
    link = await service.add_traceability_link(
        workspace_id=workspace_id,
        project_id=project_id,
        requirement_id=requirement_id,
        target_type=payload.target_type,
        target_id=payload.target_id,
        relation=payload.relation,
        actor=_actor(request),
    )
    return TraceabilityLinkResponse.from_domain(link)


@router.get("/{requirement_id}/traceability", response_model=TraceabilityResponse)
async def get_traceability(
    workspace_id: str,
    project_id: str,
    requirement_id: str,
    service: ServiceDependency,
) -> TraceabilityResponse:
    requirement = await service.get(workspace_id, project_id, requirement_id)
    links = await service.traceability(workspace_id, project_id, requirement_id)
    return _traceability_response(requirement, links)


def _traceability_response(
    requirement: Requirement,
    links: list[TraceabilityLink],
) -> TraceabilityResponse:
    target_types = {link.target_type.value for link in links}
    return TraceabilityResponse(
        requirement=RequirementResponse.from_domain(requirement),
        links=[TraceabilityLinkResponse.from_domain(link) for link in links],
        coverage={
            "feature": "FEATURE" in target_types or requirement.feature_id is not None,
            "evidence": "EVIDENCE" in target_types,
            "document": "DOCUMENT" in target_types,
            "test": "TEST" in target_types,
            "change": "CHANGE" in target_types,
        },
    )


_REQUIREMENT_ERROR_STATUS: Mapping[type[RequirementError], int] = {
    InvalidRequirementIdError: 422,
    InvalidRequirementKeyError: 422,
    InvalidRequirementTitleError: 422,
    InvalidRequirementStatementError: 422,
    InvalidRequirementAcceptanceCriteriaError: 422,
    InvalidRequirementRationaleError: 422,
    InvalidRequirementTypeError: 422,
    InvalidRequirementStatusTransitionError: 409,
    InvalidTraceabilityTargetError: 422,
    RequirementNotFoundError: 404,
    RequirementProjectNotFoundError: 404,
    RequirementWorkspaceMismatchError: 404,
    RequirementFeatureNotFoundError: 404,
    TraceabilityTargetNotFoundError: 404,
    RequirementKeyAlreadyExistsError: 409,
    TraceabilityLinkAlreadyExistsError: 409,
    RequirementProjectArchivedError: 409,
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
                "context": asdict(_ErrorContext(project="requirements")),
            }
        },
    )


class _ErrorContext(BaseModel):
    project: str
