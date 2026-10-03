from collections.abc import Mapping
from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from tdp.identity.provider import IdentityProvider
from tdp.modules.workflow.application.service import WorkflowApplicationService
from tdp.modules.workflow.domain.errors import (
    InvalidWorkflowAssigneeError,
    InvalidWorkflowCommentError,
    InvalidWorkflowEntityError,
    InvalidWorkflowItemIdError,
    InvalidWorkflowPriorityError,
    InvalidWorkflowTitleError,
    InvalidWorkflowTransitionError,
    WorkflowEntityNotFoundError,
    WorkflowError,
    WorkflowItemNotFoundError,
    WorkflowProjectArchivedError,
    WorkflowProjectNotFoundError,
    WorkflowWorkspaceMismatchError,
)
from tdp.modules.workflow.domain.model import WorkflowEvent, WorkflowItem

router = APIRouter(
    prefix="/workspaces/{workspace_id}/projects/{project_id}/workflow-items",
    tags=["workflow"],
)


class CreateWorkflowItemRequest(BaseModel):
    entity_type: str = Field(min_length=3, max_length=30)
    entity_id: str = Field(min_length=1, max_length=500)
    title: str = Field(min_length=3, max_length=240)
    priority: str = Field(default="P2", min_length=2, max_length=2)
    assignee: str = Field(default="", max_length=160)


class TransitionWorkflowItemRequest(BaseModel):
    action: str = Field(min_length=3, max_length=30)
    comment: str = Field(default="", max_length=2000)


class WorkflowItemResponse(BaseModel):
    id: str
    workspace_id: str
    project_id: str
    entity_type: str
    entity_id: str
    title: str
    priority: str
    state: str
    assignee: str
    created_by: str
    due_at: str
    created_at: str
    updated_at: str
    overdue: bool

    @classmethod
    def from_domain(cls, item: WorkflowItem) -> "WorkflowItemResponse":
        from datetime import UTC, datetime

        return cls(
            id=str(item.id),
            workspace_id=item.workspace_id,
            project_id=item.project_id,
            entity_type=item.entity_type.value,
            entity_id=item.entity_id,
            title=item.title,
            priority=item.priority.value,
            state=item.state.value,
            assignee=item.assignee,
            created_by=item.created_by,
            due_at=item.due_at.isoformat(),
            created_at=item.created_at.isoformat(),
            updated_at=item.updated_at.isoformat(),
            overdue=item.due_at < datetime.now(UTC)
            and item.state.value not in {"CLOSED", "CANCELLED"},
        )


class WorkflowCollectionResponse(BaseModel):
    items: list[WorkflowItemResponse]
    total: int


class WorkflowEventResponse(BaseModel):
    id: str
    workflow_item_id: str
    action: str
    previous_state: str
    new_state: str
    actor: str
    comment: str
    created_at: str

    @classmethod
    def from_domain(cls, event: WorkflowEvent) -> "WorkflowEventResponse":
        return cls(
            id=str(event.id),
            workflow_item_id=str(event.workflow_item_id),
            action=event.action.value,
            previous_state=event.previous_state.value,
            new_state=event.new_state.value,
            actor=event.actor,
            comment=event.comment,
            created_at=event.created_at.isoformat(),
        )


class WorkflowHistoryResponse(BaseModel):
    items: list[WorkflowEventResponse]
    total: int


def get_service(request: Request) -> WorkflowApplicationService:
    return cast(WorkflowApplicationService, request.app.state.workflow_service)


ServiceDependency = Annotated[WorkflowApplicationService, Depends(get_service)]


def _actor(request: Request) -> str:
    provider = cast(IdentityProvider, request.app.state.identity_provider)
    return provider.current_principal().audit_actor


@router.post("", response_model=WorkflowItemResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow_item(
    workspace_id: str,
    project_id: str,
    payload: CreateWorkflowItemRequest,
    request: Request,
    service: ServiceDependency,
) -> WorkflowItemResponse:
    item = await service.create(
        workspace_id=workspace_id,
        project_id=project_id,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        title=payload.title,
        priority=payload.priority,
        assignee=payload.assignee,
        actor=_actor(request),
    )
    return WorkflowItemResponse.from_domain(item)


@router.get("", response_model=WorkflowCollectionResponse)
async def list_workflow_items(
    workspace_id: str,
    project_id: str,
    service: ServiceDependency,
) -> WorkflowCollectionResponse:
    items = await service.list_items(workspace_id, project_id)
    responses = [WorkflowItemResponse.from_domain(item) for item in items]
    return WorkflowCollectionResponse(items=responses, total=len(responses))


@router.get("/{item_id}", response_model=WorkflowItemResponse)
async def get_workflow_item(
    workspace_id: str,
    project_id: str,
    item_id: str,
    service: ServiceDependency,
) -> WorkflowItemResponse:
    return WorkflowItemResponse.from_domain(
        await service.get(workspace_id, project_id, item_id)
    )


@router.post("/{item_id}/transition", response_model=WorkflowItemResponse)
async def transition_workflow_item(
    workspace_id: str,
    project_id: str,
    item_id: str,
    payload: TransitionWorkflowItemRequest,
    request: Request,
    service: ServiceDependency,
) -> WorkflowItemResponse:
    item = await service.transition(
        workspace_id=workspace_id,
        project_id=project_id,
        item_id=item_id,
        action=payload.action,
        comment=payload.comment,
        actor=_actor(request),
    )
    return WorkflowItemResponse.from_domain(item)


@router.get("/{item_id}/history", response_model=WorkflowHistoryResponse)
async def workflow_history(
    workspace_id: str,
    project_id: str,
    item_id: str,
    service: ServiceDependency,
) -> WorkflowHistoryResponse:
    events = await service.history(workspace_id, project_id, item_id)
    responses = [WorkflowEventResponse.from_domain(item) for item in events]
    return WorkflowHistoryResponse(items=responses, total=len(responses))


_WORKFLOW_ERROR_STATUS: Mapping[type[WorkflowError], int] = {
    InvalidWorkflowItemIdError: 422,
    InvalidWorkflowEntityError: 422,
    InvalidWorkflowTitleError: 422,
    InvalidWorkflowPriorityError: 422,
    InvalidWorkflowTransitionError: 409,
    InvalidWorkflowAssigneeError: 422,
    InvalidWorkflowCommentError: 422,
    WorkflowItemNotFoundError: 404,
    WorkflowEntityNotFoundError: 404,
    WorkflowProjectNotFoundError: 404,
    WorkflowWorkspaceMismatchError: 404,
    WorkflowProjectArchivedError: 409,
}


async def workflow_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, WorkflowError):
        raise exc
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=_WORKFLOW_ERROR_STATUS.get(type(exc), 400),
        content={
            "error": {
                "code": exc.code,
                "message": str(exc),
                "requestId": request_id,
            }
        },
    )
