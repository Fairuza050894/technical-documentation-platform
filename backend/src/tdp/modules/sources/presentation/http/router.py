from typing import Annotated, cast

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from pydantic import BaseModel

from tdp.modules.sources.application.commands import ImportOpenApiSourceCommand
from tdp.modules.sources.application.dto import SourceDto
from tdp.modules.sources.application.service import SourceApplicationService

router = APIRouter(tags=["sources"])


class SourceResponse(BaseModel):
    id: str
    project_id: str
    name: str
    source_type: str
    status: str
    original_file_name: str
    media_type: str
    checksum: str
    openapi_version: str
    api_title: str
    api_version: str
    path_count: int
    operation_count: int
    created_at: str
    updated_at: str

    @classmethod
    def from_dto(cls, source: SourceDto) -> "SourceResponse":
        return cls(
            id=source.id,
            project_id=source.project_id,
            name=source.name,
            source_type=source.source_type,
            status=source.status,
            original_file_name=source.original_file_name,
            media_type=source.media_type,
            checksum=source.checksum,
            openapi_version=source.openapi_version,
            api_title=source.api_title,
            api_version=source.api_version,
            path_count=source.path_count,
            operation_count=source.operation_count,
            created_at=source.created_at,
            updated_at=source.updated_at,
        )


class SourceCollectionResponse(BaseModel):
    items: list[SourceResponse]
    total: int


def get_source_service(request: Request) -> SourceApplicationService:
    return cast(SourceApplicationService, request.app.state.source_service)


SourceServiceDependency = Annotated[SourceApplicationService, Depends(get_source_service)]


@router.post(
    "/projects/{project_id}/sources/openapi",
    response_model=SourceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def import_openapi_source(
    project_id: str,
    service: SourceServiceDependency,
    name: Annotated[str, Form(min_length=3, max_length=80)],
    file: Annotated[UploadFile, File()],
) -> SourceResponse:
    try:
        content = await file.read(service.max_file_bytes + 1)
    finally:
        await file.close()
    source = await service.import_openapi(
        ImportOpenApiSourceCommand(
            project_id=project_id,
            name=name,
            file_name=file.filename or "source",
            content=content,
        )
    )
    return SourceResponse.from_dto(source)


@router.get(
    "/projects/{project_id}/sources",
    response_model=SourceCollectionResponse,
)
async def list_sources(
    project_id: str,
    service: SourceServiceDependency,
) -> SourceCollectionResponse:
    sources = await service.list_sources(project_id)
    items = [SourceResponse.from_dto(source) for source in sources]
    return SourceCollectionResponse(items=items, total=len(items))


@router.get("/sources/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: str,
    service: SourceServiceDependency,
) -> SourceResponse:
    return SourceResponse.from_dto(await service.get(source_id))


@router.post("/sources/{source_id}/archive", response_model=SourceResponse)
async def archive_source(
    source_id: str,
    service: SourceServiceDependency,
) -> SourceResponse:
    return SourceResponse.from_dto(await service.archive(source_id))
