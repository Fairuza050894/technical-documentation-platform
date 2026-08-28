from collections.abc import Mapping
from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from tdp.modules.templates.application.dto import TemplateDto, TemplateSummaryDto
from tdp.modules.templates.application.service import TemplateApplicationService
from tdp.modules.templates.domain.errors import (
    TemplateBuiltinModificationError,
    TemplateError,
    TemplateKeyConflictError,
    TemplateNotFoundError,
    TemplateValidationError,
)

router = APIRouter(tags=["templates"])


class CreateTemplateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    category: str
    standard: str
    content: str = Field(min_length=10)


class UpdateTemplateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    content: str | None = Field(default=None, min_length=10)


class DuplicateTemplateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(min_length=2, max_length=50)


class TemplateResponse(BaseModel):
    id: str
    key: str
    name: str
    description: str
    category: str
    standard: str
    content: str
    is_builtin: bool
    version: int
    created_at: str
    updated_at: str

    @classmethod
    def from_dto(cls, template: TemplateDto) -> "TemplateResponse":
        return cls(
            id=template.id,
            key=template.key,
            name=template.name,
            description=template.description,
            category=template.category,
            standard=template.standard,
            content=template.content,
            is_builtin=template.is_builtin,
            version=template.version,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )


class TemplateSummaryResponse(BaseModel):
    id: str
    key: str
    name: str
    description: str
    category: str
    standard: str
    is_builtin: bool
    version: int
    section_count: int
    created_at: str
    updated_at: str

    @classmethod
    def from_dto(cls, template: TemplateSummaryDto) -> "TemplateSummaryResponse":
        return cls(
            id=template.id,
            key=template.key,
            name=template.name,
            description=template.description,
            category=template.category,
            standard=template.standard,
            is_builtin=template.is_builtin,
            version=template.version,
            section_count=template.section_count,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )


class TemplateCollectionResponse(BaseModel):
    items: list[TemplateSummaryResponse]
    total: int


def get_template_service(request: Request) -> TemplateApplicationService:
    return cast(TemplateApplicationService, request.app.state.template_service)


TemplateServiceDependency = Annotated[TemplateApplicationService, Depends(get_template_service)]


@router.get("/templates", response_model=TemplateCollectionResponse)
async def list_templates(
    service: TemplateServiceDependency,
    category: str | None = None,
) -> TemplateCollectionResponse:
    templates = await service.list_templates(category)
    items = [TemplateSummaryResponse.from_dto(t) for t in templates]
    return TemplateCollectionResponse(items=items, total=len(items))


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    service: TemplateServiceDependency,
) -> TemplateResponse:
    return TemplateResponse.from_dto(await service.get_template(template_id))


@router.get("/templates/by-key/{key}", response_model=TemplateResponse)
async def get_template_by_key(
    key: str,
    service: TemplateServiceDependency,
) -> TemplateResponse:
    return TemplateResponse.from_dto(await service.get_template_by_key(key))


@router.post("/templates", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: CreateTemplateRequest,
    service: TemplateServiceDependency,
) -> TemplateResponse:
    return TemplateResponse.from_dto(
        await service.create_template(
            key=payload.key,
            name=payload.name,
            description=payload.description,
            category=payload.category,
            standard=payload.standard,
            content=payload.content,
        )
    )


@router.patch("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    payload: UpdateTemplateRequest,
    service: TemplateServiceDependency,
) -> TemplateResponse:
    return TemplateResponse.from_dto(
        await service.update_template(
            template_id,
            name=payload.name,
            description=payload.description,
            content=payload.content,
        )
    )


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: str,
    service: TemplateServiceDependency,
) -> None:
    await service.delete_template(template_id)


@router.post("/templates/{template_id}/duplicate", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_template(
    template_id: str,
    payload: DuplicateTemplateRequest,
    service: TemplateServiceDependency,
) -> TemplateResponse:
    return TemplateResponse.from_dto(
        await service.duplicate_template(template_id, payload.key)
    )


_TEMPLATE_ERROR_STATUS: Mapping[type[TemplateError], int] = {
    TemplateNotFoundError: 404,
    TemplateKeyConflictError: 409,
    TemplateBuiltinModificationError: 403,
    TemplateValidationError: 422,
}


async def template_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, TemplateError):
        raise exc
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=_TEMPLATE_ERROR_STATUS.get(type(exc), 400),
        content={
            "error": {
                "code": exc.code,
                "message": str(exc),
                "details": [],
                "requestId": request_id,
            }
        },
        headers={"X-Request-ID": request_id},
    )
