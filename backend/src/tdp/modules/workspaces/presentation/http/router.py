from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field

from tdp.modules.workspaces.application.commands import CreateWorkspaceCommand
from tdp.modules.workspaces.application.dto import WorkspaceDto
from tdp.modules.workspaces.application.service import WorkspaceApplicationService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


class CreateWorkspaceRequest(BaseModel):
    key: str = Field(min_length=2, max_length=20, pattern=r"^[A-Za-z][A-Za-z0-9-]+$")
    name: str = Field(min_length=3, max_length=80)
    description: str = Field(default="", max_length=500)


class WorkspaceResponse(BaseModel):
    id: str
    key: str
    name: str
    description: str
    status: str
    created_at: str
    updated_at: str

    @classmethod
    def from_dto(cls, workspace: WorkspaceDto) -> "WorkspaceResponse":
        return cls(
            id=workspace.id,
            key=workspace.key,
            name=workspace.name,
            description=workspace.description,
            status=workspace.status,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
        )


class WorkspaceCollectionResponse(BaseModel):
    items: list[WorkspaceResponse]
    total: int


def get_workspace_service(request: Request) -> WorkspaceApplicationService:
    return cast(WorkspaceApplicationService, request.app.state.workspace_service)


WorkspaceServiceDependency = Annotated[
    WorkspaceApplicationService,
    Depends(get_workspace_service),
]


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: CreateWorkspaceRequest,
    service: WorkspaceServiceDependency,
) -> WorkspaceResponse:
    workspace = await service.create(
        CreateWorkspaceCommand(
            key=payload.key,
            name=payload.name,
            description=payload.description,
        )
    )
    return WorkspaceResponse.from_dto(workspace)


@router.get("", response_model=WorkspaceCollectionResponse)
async def list_workspaces(
    service: WorkspaceServiceDependency,
) -> WorkspaceCollectionResponse:
    workspaces = await service.list_workspaces()
    items = [WorkspaceResponse.from_dto(workspace) for workspace in workspaces]
    return WorkspaceCollectionResponse(items=items, total=len(items))


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    service: WorkspaceServiceDependency,
) -> WorkspaceResponse:
    return WorkspaceResponse.from_dto(await service.get(workspace_id))


@router.post("/{workspace_id}/archive", response_model=WorkspaceResponse)
async def archive_workspace(
    workspace_id: str,
    service: WorkspaceServiceDependency,
) -> WorkspaceResponse:
    return WorkspaceResponse.from_dto(await service.archive(workspace_id))
