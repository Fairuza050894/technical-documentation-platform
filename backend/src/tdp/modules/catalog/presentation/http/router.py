from dataclasses import asdict
from typing import Annotated, cast

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel

from tdp.modules.catalog.application.dto import (
    ApiOperationDto,
    ApiSchemaDto,
    CatalogDto,
    SynchronizationDto,
)
from tdp.modules.catalog.application.service import CatalogApplicationService

router = APIRouter(tags=["api-catalog"])


class SynchronizationResponse(BaseModel):
    id: str
    project_id: str
    source_id: str
    source_checksum: str
    status: str
    operation_count: int
    schema_count: int
    error_code: str
    error_message: str
    started_at: str
    completed_at: str | None

    @classmethod
    def from_dto(cls, run: SynchronizationDto) -> "SynchronizationResponse":
        return cls.model_validate(asdict(run))


class SynchronizationCollectionResponse(BaseModel):
    items: list[SynchronizationResponse]
    total: int


class ApiParameterResponse(BaseModel):
    name: str
    location: str
    required: bool
    schema_type: str
    schema_format: str
    schema_reference: str


class ApiPayloadResponse(BaseModel):
    required: bool
    media_types: list[str]
    schema_types: list[str]
    schema_references: list[str]


class ApiResponseDefinition(BaseModel):
    status_code: str
    description: str
    media_types: list[str]
    schema_types: list[str]
    schema_references: list[str]


class ApiOperationResponse(BaseModel):
    synchronization_id: str
    project_id: str
    source_id: str
    method: str
    path: str
    operation_id: str
    summary: str
    description: str
    tags: list[str]
    deprecated: bool
    security_schemes: list[str]
    parameters: list[ApiParameterResponse]
    request_body: ApiPayloadResponse | None
    responses: list[ApiResponseDefinition]
    source_pointer: str

    @classmethod
    def from_dto(cls, operation: ApiOperationDto) -> "ApiOperationResponse":
        return cls.model_validate(asdict(operation))


class ApiSchemaPropertyResponse(BaseModel):
    name: str
    schema_type: str
    schema_format: str
    required: bool
    reference: str
    description: str


class ApiSchemaResponse(BaseModel):
    synchronization_id: str
    project_id: str
    source_id: str
    name: str
    schema_type: str
    description: str
    required_fields: list[str]
    properties: list[ApiSchemaPropertyResponse]
    source_pointer: str

    @classmethod
    def from_dto(cls, schema: ApiSchemaDto) -> "ApiSchemaResponse":
        return cls.model_validate(asdict(schema))


class CatalogResponse(BaseModel):
    runs: list[SynchronizationResponse]
    operations: list[ApiOperationResponse]
    schemas: list[ApiSchemaResponse]
    operation_total: int
    schema_total: int

    @classmethod
    def from_dto(cls, catalog: CatalogDto) -> "CatalogResponse":
        operations = [ApiOperationResponse.from_dto(operation) for operation in catalog.operations]
        schemas = [ApiSchemaResponse.from_dto(schema) for schema in catalog.schemas]
        return cls(
            runs=[SynchronizationResponse.from_dto(run) for run in catalog.runs],
            operations=operations,
            schemas=schemas,
            operation_total=len(operations),
            schema_total=len(schemas),
        )


def get_catalog_service(request: Request) -> CatalogApplicationService:
    return cast(CatalogApplicationService, request.app.state.catalog_service)


CatalogServiceDependency = Annotated[CatalogApplicationService, Depends(get_catalog_service)]


@router.post(
    "/sources/{source_id}/synchronizations",
    response_model=SynchronizationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def synchronize_source(
    source_id: str,
    service: CatalogServiceDependency,
) -> SynchronizationResponse:
    return SynchronizationResponse.from_dto(await service.synchronize(source_id))


@router.get(
    "/sources/{source_id}/synchronizations",
    response_model=SynchronizationCollectionResponse,
)
async def list_source_synchronizations(
    source_id: str,
    service: CatalogServiceDependency,
) -> SynchronizationCollectionResponse:
    runs = await service.list_runs(source_id)
    items = [SynchronizationResponse.from_dto(run) for run in runs]
    return SynchronizationCollectionResponse(items=items, total=len(items))


@router.get(
    "/synchronizations/{run_id}",
    response_model=SynchronizationResponse,
)
async def get_synchronization(
    run_id: str,
    service: CatalogServiceDependency,
) -> SynchronizationResponse:
    return SynchronizationResponse.from_dto(await service.get_run(run_id))


@router.get(
    "/projects/{project_id}/api-catalog",
    response_model=CatalogResponse,
)
async def get_api_catalog(
    project_id: str,
    service: CatalogServiceDependency,
    source_id: Annotated[str | None, Query()] = None,
) -> CatalogResponse:
    return CatalogResponse.from_dto(await service.get_catalog(project_id, source_id=source_id))
