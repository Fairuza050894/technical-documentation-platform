from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field

from tdp.modules.projects.application.commands import CreateProjectCommand
from tdp.modules.projects.application.dto import ProjectDto
from tdp.modules.projects.application.service import ProjectApplicationService

router = APIRouter(prefix="/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    key: str = Field(min_length=2, max_length=20, pattern=r"^[A-Za-z][A-Za-z0-9-]+$")
    name: str = Field(min_length=3, max_length=80)
    description: str = Field(default="", max_length=500)
    workspace_type: Literal["DEMO", "PERSONAL", "ENTERPRISE"] = "PERSONAL"


class ProjectResponse(BaseModel):
    id: str
    key: str
    name: str
    description: str
    workspace_type: str
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
    project = await service.create(
        CreateProjectCommand(
            key=payload.key,
            name=payload.name,
            description=payload.description,
            workspace_type=payload.workspace_type,
        )
    )
    return ProjectResponse.from_dto(project)


@router.get("", response_model=ProjectCollectionResponse)
async def list_projects(service: ProjectServiceDependency) -> ProjectCollectionResponse:
    projects = await service.list_projects()
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
