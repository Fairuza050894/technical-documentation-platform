from dataclasses import asdict
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field

from tdp.modules.governance.application.service import GovernanceApplicationService
from tdp.modules.governance.domain.model import (
    ChangeSurface,
    RequirementStatus,
    RequirementType,
    TraceTargetType,
    WorkflowState,
)
from tdp.modules.governance.infrastructure.sqlite_repository import SqliteGovernanceRepository
from tdp.modules.projects.application.service import ProjectApplicationService
from tdp.presentation.http.dependencies.identity import PrincipalDependency

router = APIRouter(tags=["governance"])


class CreateRequirementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_type: RequirementType
    title: str = Field(min_length=3, max_length=160)
    statement: str = Field(min_length=3, max_length=2000)
    rationale: str = Field(min_length=3, max_length=1000)


class CreateRequirementRevisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=160)
    statement: str = Field(min_length=3, max_length=2000)
    rationale: str = Field(min_length=3, max_length=1000)
    status: RequirementStatus | None = None


class CreateTraceLinkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: str
    target_type: TraceTargetType
    target_id: str = Field(min_length=1, max_length=200)
    relation: str = Field(min_length=1, max_length=80)


class CreateImpactAssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    change_reference: str = Field(min_length=1, max_length=300)
    surface: ChangeSurface


class CreateWorkflowCaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    impact_assessment_id: str
    owner: str = Field(min_length=2, max_length=120)


class TransitionWorkflowCaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_state: WorkflowState
    comment: str = Field(default="", max_length=500)


def get_governance_service(request: Request) -> GovernanceApplicationService:
    settings = request.app.state.settings
    project_service = cast(ProjectApplicationService, request.app.state.project_service)
    repository = SqliteGovernanceRepository(settings.database_path)
    return GovernanceApplicationService(repository, project_service)


GovernanceServiceDependency = Annotated[
    GovernanceApplicationService,
    Depends(get_governance_service),
]


def _payload(value: Any) -> Any:
    return jsonable_encoder(asdict(value))


@router.post(
    "/projects/{project_id}/requirements",
    status_code=status.HTTP_201_CREATED,
)
async def create_requirement(
    project_id: str,
    payload: CreateRequirementRequest,
    service: GovernanceServiceDependency,
    principal: PrincipalDependency,
) -> Any:
    try:
        requirement = await service.create_requirement(
            project_id=project_id,
            requirement_type=payload.requirement_type,
            title=payload.title,
            statement=payload.statement,
            rationale=payload.rationale,
            actor=principal.audit_actor,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _payload(requirement)


@router.get("/projects/{project_id}/requirements")
async def list_requirements(
    project_id: str,
    service: GovernanceServiceDependency,
) -> dict[str, Any]:
    items = await service.list_requirements(project_id)
    return {"items": [_payload(item) for item in items], "total": len(items)}


@router.post(
    "/requirements/{requirement_id}/revisions",
    status_code=status.HTTP_201_CREATED,
)
async def create_requirement_revision(
    requirement_id: str,
    payload: CreateRequirementRevisionRequest,
    service: GovernanceServiceDependency,
    principal: PrincipalDependency,
) -> Any:
    try:
        revision = await service.create_requirement_revision(
            requirement_id=requirement_id,
            title=payload.title,
            statement=payload.statement,
            rationale=payload.rationale,
            actor=principal.audit_actor,
            status=payload.status,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _payload(revision)


@router.post(
    "/projects/{project_id}/trace-links",
    status_code=status.HTTP_201_CREATED,
)
async def create_trace_link(
    project_id: str,
    payload: CreateTraceLinkRequest,
    service: GovernanceServiceDependency,
    principal: PrincipalDependency,
) -> Any:
    try:
        link = await service.create_trace_link(
            project_id=project_id,
            requirement_id=payload.requirement_id,
            target_type=payload.target_type,
            target_id=payload.target_id,
            relation=payload.relation,
            actor=principal.audit_actor,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _payload(link)


@router.get("/projects/{project_id}/traceability")
async def traceability_summary(
    project_id: str,
    service: GovernanceServiceDependency,
) -> Any:
    return jsonable_encoder(await service.traceability_summary(project_id))


@router.post(
    "/projects/{project_id}/impact-assessments",
    status_code=status.HTTP_201_CREATED,
)
async def create_impact_assessment(
    project_id: str,
    payload: CreateImpactAssessmentRequest,
    service: GovernanceServiceDependency,
    principal: PrincipalDependency,
) -> Any:
    assessment = await service.assess_impact(
        project_id=project_id,
        change_reference=payload.change_reference,
        surface=payload.surface,
        actor=principal.audit_actor,
    )
    return _payload(assessment)


@router.post(
    "/projects/{project_id}/workflow-cases",
    status_code=status.HTTP_201_CREATED,
)
async def create_workflow_case(
    project_id: str,
    payload: CreateWorkflowCaseRequest,
    service: GovernanceServiceDependency,
    principal: PrincipalDependency,
) -> Any:
    try:
        case = await service.create_workflow_case(
            project_id=project_id,
            impact_assessment_id=payload.impact_assessment_id,
            owner=payload.owner,
            actor=principal.audit_actor,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _payload(case)


@router.post("/workflow-cases/{case_id}/transitions")
async def transition_workflow_case(
    case_id: str,
    payload: TransitionWorkflowCaseRequest,
    service: GovernanceServiceDependency,
    principal: PrincipalDependency,
) -> Any:
    try:
        case = await service.transition_workflow_case(
            case_id=case_id,
            target=payload.target_state,
            actor=principal.audit_actor,
            comment=payload.comment,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _payload(case)


@router.get("/projects/{project_id}/governance-summary")
async def governance_summary(
    project_id: str,
    service: GovernanceServiceDependency,
) -> Any:
    return jsonable_encoder(await service.governance_summary(project_id))
