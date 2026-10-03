from collections.abc import Mapping
from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from tdp.modules.governance.application.service import GovernanceApplicationService
from tdp.modules.governance.domain.errors import (
    GovernanceError,
    ImpactAssessmentNotFoundError,
    InvalidRequirementError,
    InvalidTraceLinkError,
    InvalidWorkflowTransitionError,
    RequirementKeyAlreadyExistsError,
    RequirementNotFoundError,
)
from tdp.modules.governance.domain.model import (
    ImpactAssessment,
    RequirementKind,
    RequirementRevision,
    TraceLink,
    TraceRelation,
    TraceTargetType,
    WorkflowAction,
    WorkflowEvent,
)
from tdp.presentation.http.dependencies.identity import PrincipalDependency

router = APIRouter(
    prefix="/workspaces/{workspace_id}/projects/{project_id}/governance",
    tags=["governance"],
)


class CreateRequirementRequest(BaseModel):
    key: str = Field(min_length=2, max_length=40)
    kind: RequirementKind
    title: str = Field(min_length=3, max_length=160)
    statement: str = Field(min_length=10, max_length=4000)
    acceptance_criteria: list[str] = Field(default_factory=list, max_length=50)
    owner: str = Field(min_length=1, max_length=160)


class ReviseRequirementRequest(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    statement: str = Field(min_length=10, max_length=4000)
    acceptance_criteria: list[str] = Field(default_factory=list, max_length=50)
    owner: str = Field(min_length=1, max_length=160)


class RequirementResponse(BaseModel):
    id: str
    key: str
    revision: int
    kind: str
    title: str
    statement: str
    acceptance_criteria: list[str]
    owner: str
    status: str
    previous_revision_id: str | None
    created_by: str
    created_at: str

    @classmethod
    def from_domain(cls, value: RequirementRevision) -> "RequirementResponse":
        return cls(
            id=value.id,
            key=value.key,
            revision=value.revision,
            kind=value.kind.value,
            title=value.title,
            statement=value.statement,
            acceptance_criteria=list(value.acceptance_criteria),
            owner=value.owner,
            status=value.status.value,
            previous_revision_id=value.previous_revision_id,
            created_by=value.created_by,
            created_at=value.created_at.isoformat(),
        )


class RequirementCollectionResponse(BaseModel):
    items: list[RequirementResponse]
    total: int


class CreateTraceLinkRequest(BaseModel):
    requirement_revision_id: str
    target_type: TraceTargetType
    target_id: str = Field(min_length=1, max_length=500)
    relation: TraceRelation
    rationale: str = Field(default="", max_length=1000)


class TraceLinkResponse(BaseModel):
    id: str
    requirement_revision_id: str
    target_type: str
    target_id: str
    relation: str
    rationale: str
    created_by: str
    created_at: str

    @classmethod
    def from_domain(cls, value: TraceLink) -> "TraceLinkResponse":
        return cls(
            id=value.id,
            requirement_revision_id=value.requirement_revision_id,
            target_type=value.target_type.value,
            target_id=value.target_id,
            relation=value.relation.value,
            rationale=value.rationale,
            created_by=value.created_by,
            created_at=value.created_at.isoformat(),
        )


class TraceLinkCollectionResponse(BaseModel):
    items: list[TraceLinkResponse]
    total: int


class EvaluateImpactRequest(BaseModel):
    change_reference: str = Field(min_length=1, max_length=500)
    changed_target_type: TraceTargetType
    changed_target_id: str = Field(min_length=1, max_length=500)


class ImpactResponse(BaseModel):
    id: str
    change_reference: str
    changed_target_type: str
    changed_target_id: str
    severity: str
    impacted_requirement_ids: list[str]
    required_actions: list[str]
    workflow_state: str
    rationale: str
    created_by: str
    created_at: str
    updated_at: str

    @classmethod
    def from_domain(cls, value: ImpactAssessment) -> "ImpactResponse":
        return cls(
            id=value.id,
            change_reference=value.change_reference,
            changed_target_type=value.changed_target_type.value,
            changed_target_id=value.changed_target_id,
            severity=value.severity.value,
            impacted_requirement_ids=list(value.impacted_requirement_ids),
            required_actions=list(value.required_actions),
            workflow_state=value.workflow_state.value,
            rationale=value.rationale,
            created_by=value.created_by,
            created_at=value.created_at.isoformat(),
            updated_at=value.updated_at.isoformat(),
        )


class ImpactCollectionResponse(BaseModel):
    items: list[ImpactResponse]
    total: int


class TransitionImpactRequest(BaseModel):
    action: WorkflowAction
    comment: str = Field(default="", max_length=2000)


class WorkflowEventResponse(BaseModel):
    id: str
    assessment_id: str
    action: str
    previous_state: str
    new_state: str
    actor: str
    comment: str
    created_at: str

    @classmethod
    def from_domain(cls, value: WorkflowEvent) -> "WorkflowEventResponse":
        return cls(
            id=value.id,
            assessment_id=value.assessment_id,
            action=value.action.value,
            previous_state=value.previous_state.value,
            new_state=value.new_state.value,
            actor=value.actor,
            comment=value.comment,
            created_at=value.created_at.isoformat(),
        )


class TransitionImpactResponse(BaseModel):
    assessment: ImpactResponse
    event: WorkflowEventResponse


class WorkflowEventCollectionResponse(BaseModel):
    items: list[WorkflowEventResponse]
    total: int


def get_governance_service(request: Request) -> GovernanceApplicationService:
    return cast(GovernanceApplicationService, request.app.state.governance_service)


GovernanceServiceDependency = Annotated[
    GovernanceApplicationService,
    Depends(get_governance_service),
]


@router.post(
    "/requirements",
    response_model=RequirementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_requirement(
    workspace_id: str,
    project_id: str,
    payload: CreateRequirementRequest,
    service: GovernanceServiceDependency,
    principal: PrincipalDependency,
) -> RequirementResponse:
    value = await service.create_requirement(
        workspace_id=workspace_id,
        project_id=project_id,
        key=payload.key,
        kind=payload.kind,
        title=payload.title,
        statement=payload.statement,
        acceptance_criteria=tuple(payload.acceptance_criteria),
        owner=payload.owner,
        principal=principal,
    )
    return RequirementResponse.from_domain(value)


@router.get("/requirements", response_model=RequirementCollectionResponse)
async def list_requirements(
    workspace_id: str,
    project_id: str,
    service: GovernanceServiceDependency,
) -> RequirementCollectionResponse:
    values = await service.list_requirements(workspace_id, project_id)
    items = [RequirementResponse.from_domain(item) for item in values]
    return RequirementCollectionResponse(items=items, total=len(items))


@router.post(
    "/requirements/{key}/revisions",
    response_model=RequirementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def revise_requirement(
    workspace_id: str,
    project_id: str,
    key: str,
    payload: ReviseRequirementRequest,
    service: GovernanceServiceDependency,
    principal: PrincipalDependency,
) -> RequirementResponse:
    value = await service.revise_requirement(
        workspace_id=workspace_id,
        project_id=project_id,
        key=key,
        title=payload.title,
        statement=payload.statement,
        acceptance_criteria=tuple(payload.acceptance_criteria),
        owner=payload.owner,
        principal=principal,
    )
    return RequirementResponse.from_domain(value)


@router.post(
    "/trace-links",
    response_model=TraceLinkResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_trace_link(
    workspace_id: str,
    project_id: str,
    payload: CreateTraceLinkRequest,
    service: GovernanceServiceDependency,
    principal: PrincipalDependency,
) -> TraceLinkResponse:
    value = await service.add_trace_link(
        workspace_id=workspace_id,
        project_id=project_id,
        requirement_revision_id=payload.requirement_revision_id,
        target_type=payload.target_type,
        target_id=payload.target_id,
        relation=payload.relation,
        rationale=payload.rationale,
        principal=principal,
    )
    return TraceLinkResponse.from_domain(value)


@router.get("/trace-links", response_model=TraceLinkCollectionResponse)
async def list_trace_links(
    workspace_id: str,
    project_id: str,
    service: GovernanceServiceDependency,
) -> TraceLinkCollectionResponse:
    values = await service.list_trace_links(workspace_id, project_id)
    items = [TraceLinkResponse.from_domain(item) for item in values]
    return TraceLinkCollectionResponse(items=items, total=len(items))


@router.post(
    "/impacts/evaluate",
    response_model=ImpactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def evaluate_impact(
    workspace_id: str,
    project_id: str,
    payload: EvaluateImpactRequest,
    service: GovernanceServiceDependency,
    principal: PrincipalDependency,
) -> ImpactResponse:
    value = await service.evaluate_impact(
        workspace_id=workspace_id,
        project_id=project_id,
        change_reference=payload.change_reference,
        changed_target_type=payload.changed_target_type,
        changed_target_id=payload.changed_target_id,
        principal=principal,
    )
    return ImpactResponse.from_domain(value)


@router.get("/impacts", response_model=ImpactCollectionResponse)
async def list_impacts(
    workspace_id: str,
    project_id: str,
    service: GovernanceServiceDependency,
) -> ImpactCollectionResponse:
    values = await service.list_impacts(workspace_id, project_id)
    items = [ImpactResponse.from_domain(item) for item in values]
    return ImpactCollectionResponse(items=items, total=len(items))


@router.post(
    "/impacts/{assessment_id}/transitions",
    response_model=TransitionImpactResponse,
)
async def transition_impact(
    workspace_id: str,
    project_id: str,
    assessment_id: str,
    payload: TransitionImpactRequest,
    service: GovernanceServiceDependency,
    principal: PrincipalDependency,
) -> TransitionImpactResponse:
    assessment, event = await service.transition_impact(
        workspace_id=workspace_id,
        project_id=project_id,
        assessment_id=assessment_id,
        action=payload.action,
        comment=payload.comment,
        principal=principal,
    )
    return TransitionImpactResponse(
        assessment=ImpactResponse.from_domain(assessment),
        event=WorkflowEventResponse.from_domain(event),
    )


@router.get(
    "/impacts/{assessment_id}/events",
    response_model=WorkflowEventCollectionResponse,
)
async def list_workflow_events(
    workspace_id: str,
    project_id: str,
    assessment_id: str,
    service: GovernanceServiceDependency,
) -> WorkflowEventCollectionResponse:
    values = await service.list_workflow_events(
        workspace_id=workspace_id,
        project_id=project_id,
        assessment_id=assessment_id,
    )
    items = [WorkflowEventResponse.from_domain(item) for item in values]
    return WorkflowEventCollectionResponse(items=items, total=len(items))


_GOVERNANCE_ERROR_STATUS: Mapping[type[GovernanceError], int] = {
    InvalidRequirementError: 422,
    InvalidTraceLinkError: 422,
    InvalidWorkflowTransitionError: 409,
    RequirementKeyAlreadyExistsError: 409,
    RequirementNotFoundError: 404,
    ImpactAssessmentNotFoundError: 404,
}


async def governance_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, GovernanceError):
        raise exc
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=_GOVERNANCE_ERROR_STATUS.get(type(exc), 400),
        content={
            "error": {
                "code": exc.code,
                "message": str(exc),
                "requestId": request_id,
            }
        },
    )
