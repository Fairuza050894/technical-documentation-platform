from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel, Field

from tdp.modules.projects.application.commands import CreateProjectCommand
from tdp.modules.projects.application.dto import ProjectDto
from tdp.modules.projects.application.service import ProjectApplicationService

router = APIRouter(prefix="/projects", tags=["projects"])
workspace_projects_router = APIRouter(
    prefix="/workspaces/{workspace_id}/projects",
    tags=["projects"],
)


class CreateProjectRequest(BaseModel):
    key: str = Field(min_length=2, max_length=20, pattern=r"^[A-Za-z][A-Za-z0-9-]+$")
    name: str = Field(min_length=3, max_length=80)
    description: str = Field(default="", max_length=500)
    ownership_type: Literal["PERSONAL", "TEAM"] | None = None
    workspace_id: str | None = None
    workspace_type: Literal["DEMO", "PERSONAL", "ENTERPRISE"] | None = None

    def to_command(self, *, workspace_id: str | None = None) -> CreateProjectCommand:
        return CreateProjectCommand(
            key=self.key,
            name=self.name,
            description=self.description,
            workspace_type=self.workspace_type or "PERSONAL",
            workspace_id=workspace_id or self.workspace_id,
            ownership_type=self.ownership_type,
        )


class ProjectResponse(BaseModel):
    id: str
    key: str
    name: str
    description: str
    workspace_type: str
    workspace_id: str
    ownership_type: str
    status: str
    created_at: str
    updated_at: str

    @classmethod
    def from_dto(cls, project: ProjectDto) -> "ProjectResponse":
        return cls(
            id=project.id,
            key=project.key,
            name=project.name,
            description=project.description,
            workspace_type=project.workspace_type,
            workspace_id=project.workspace_id,
            ownership_type=project.ownership_type,
            status=project.status,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )


class ProjectCollectionResponse(BaseModel):
    items: list[ProjectResponse]
    total: int


def get_project_service(request: Request) -> ProjectApplicationService:
    return cast(ProjectApplicationService, request.app.state.project_service)


ProjectServiceDependency = Annotated[ProjectApplicationService, Depends(get_project_service)]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: CreateProjectRequest,
    service: ProjectServiceDependency,
) -> ProjectResponse:
    project = await service.create(payload.to_command())
    return ProjectResponse.from_dto(project)


@router.get("", response_model=ProjectCollectionResponse)
async def list_projects(
    service: ProjectServiceDependency,
    workspace_id: str | None = Query(default=None),
) -> ProjectCollectionResponse:
    projects = await service.list_projects(workspace_id)
    items = [ProjectResponse.from_dto(project) for project in projects]
    return ProjectCollectionResponse(items=items, total=len(items))


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    service: ProjectServiceDependency,
) -> ProjectResponse:
    return ProjectResponse.from_dto(await service.get(project_id))


@router.post("/{project_id}/archive", response_model=ProjectResponse)
async def archive_project(
    project_id: str,
    service: ProjectServiceDependency,
) -> ProjectResponse:
    return ProjectResponse.from_dto(await service.archive(project_id))


@workspace_projects_router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workspace_project(
    workspace_id: str,
    payload: CreateProjectRequest,
    service: ProjectServiceDependency,
) -> ProjectResponse:
    project = await service.create(payload.to_command(workspace_id=workspace_id))
    return ProjectResponse.from_dto(project)


@workspace_projects_router.get("", response_model=ProjectCollectionResponse)
async def list_workspace_projects(
    workspace_id: str,
    service: ProjectServiceDependency,
) -> ProjectCollectionResponse:
    projects = await service.list_projects(workspace_id)
    items = [ProjectResponse.from_dto(project) for project in projects]
    return ProjectCollectionResponse(items=items, total=len(items))
