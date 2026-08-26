from datetime import UTC, datetime
from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field

from tdp.authorization.model import Role
from tdp.modules.workspaces.application.commands import CreateWorkspaceCommand, UpdateWorkspaceCommand
from tdp.modules.workspaces.application.dto import WorkspaceDto
from tdp.modules.workspaces.application.service import WorkspaceApplicationService
from tdp.modules.workspaces.domain.membership import WorkspaceMember
from tdp.modules.workspaces.infrastructure.membership_repository import SqliteMembershipRepository
from tdp.presentation.http.dependencies.identity import PrincipalDependency

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


# ── Request / Response models ──


class CreateWorkspaceRequest(BaseModel):
    key: str = Field(min_length=2, max_length=20, pattern=r"^[A-Za-z][A-Za-z0-9-]+$")
    name: str = Field(min_length=3, max_length=80)
    description: str = Field(default="", max_length=500)


class UpdateWorkspaceRequest(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=80)
    description: str | None = Field(default=None, max_length=500)


class AddMemberRequest(BaseModel):
    subject_id: str = Field(min_length=2, max_length=48)
    role: str = Field(
        description="Role: admin, document_author, reviewer, approver, viewer",
    )


class RemoveMemberRequest(BaseModel):
    subject_id: str
    role: str


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


class MemberResponse(BaseModel):
    workspace_id: str
    subject_id: str
    role: str
    added_at: str
    added_by: str


class MemberCollectionResponse(BaseModel):
    items: list[MemberResponse]
    total: int


# ── Dependencies ──


def get_workspace_service(request: Request) -> WorkspaceApplicationService:
    return cast(WorkspaceApplicationService, request.app.state.workspace_service)


def get_membership_repository(request: Request) -> SqliteMembershipRepository:
    return cast(SqliteMembershipRepository, request.app.state.membership_repository)


WorkspaceServiceDependency = Annotated[
    WorkspaceApplicationService,
    Depends(get_workspace_service),
]

MembershipRepositoryDependency = Annotated[
    SqliteMembershipRepository,
    Depends(get_membership_repository),
]


# ── Workspace CRUD ──


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


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str,
    payload: UpdateWorkspaceRequest,
    service: WorkspaceServiceDependency,
) -> WorkspaceResponse:
    return WorkspaceResponse.from_dto(
        await service.update(
            workspace_id,
            UpdateWorkspaceCommand(
                name=payload.name,
                description=payload.description,
            ),
        )
    )


@router.post("/{workspace_id}/archive", response_model=WorkspaceResponse)
async def archive_workspace(
    workspace_id: str,
    service: WorkspaceServiceDependency,
) -> WorkspaceResponse:
    return WorkspaceResponse.from_dto(await service.archive(workspace_id))


# ── Membership ──


@router.get("/{workspace_id}/members", response_model=MemberCollectionResponse)
async def list_workspace_members(
    workspace_id: str,
    repo: MembershipRepositoryDependency,
) -> MemberCollectionResponse:
    members = repo.list_members(workspace_id)
    items = [
        MemberResponse(
            workspace_id=m.workspace_id,
            subject_id=m.subject_id,
            role=m.role.value,
            added_at=m.added_at.isoformat(),
            added_by=m.added_by,
        )
        for m in members
    ]
    return MemberCollectionResponse(items=items, total=len(items))


@router.post(
    "/{workspace_id}/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_workspace_member(
    workspace_id: str,
    payload: AddMemberRequest,
    repo: MembershipRepositoryDependency,
    principal: PrincipalDependency,
) -> MemberResponse:
    # Validate role against the Role enum
    try:
        role = Role(payload.role)
    except ValueError:
        valid_roles = [r.value for r in Role]
        from fastapi import HTTPException
        raise HTTPException(
            status_code=422,
            detail=f"Invalid role '{payload.role}'. Valid roles: {valid_roles}",
        )

    member = WorkspaceMember(
        workspace_id=workspace_id,
        subject_id=payload.subject_id,
        role=role,
        added_at=datetime.now(UTC),
        added_by=principal.subject_id,
    )
    repo.add_member(member)
    return MemberResponse(
        workspace_id=member.workspace_id,
        subject_id=member.subject_id,
        role=member.role.value,
        added_at=member.added_at.isoformat(),
        added_by=member.added_by,
    )


@router.delete("/{workspace_id}/members", status_code=status.HTTP_204_NO_CONTENT)
async def remove_workspace_member(
    workspace_id: str,
    payload: RemoveMemberRequest,
    repo: MembershipRepositoryDependency,
) -> None:
    try:
        role = Role(payload.role)
    except ValueError:
        valid_roles = [r.value for r in Role]
        from fastapi import HTTPException
        raise HTTPException(
            status_code=422,
            detail=f"Invalid role '{payload.role}'. Valid roles: {valid_roles}",
        )
    repo.remove_member(workspace_id, payload.subject_id, role)