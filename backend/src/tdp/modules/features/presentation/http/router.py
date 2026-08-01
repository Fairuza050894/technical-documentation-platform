from collections.abc import Mapping
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from tdp.modules.features.application.commands import CreateFeatureCommand
from tdp.modules.features.application.dto import (
    FeatureDocumentationMapItemDto,
    FeatureDto,
)
from tdp.modules.features.application.service import FeatureApplicationService
from tdp.modules.features.domain.errors import (
    FeatureAlreadyArchivedError,
    FeatureError,
    FeatureKeyAlreadyExistsError,
    FeatureNotFoundError,
    FeatureProjectArchivedError,
    FeatureProjectNotFoundError,
    FeatureWorkspaceMismatchError,
    InvalidFeatureDescriptionError,
    InvalidFeatureIdError,
    InvalidFeatureKeyError,
    InvalidFeatureKindError,
    InvalidFeatureNameError,
    InvalidFeatureOwnerError,
    InvalidFeatureProjectIdError,
)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/projects/{project_id}/features",
    tags=["features"],
)


class CreateFeatureRequest(BaseModel):
    key: str = Field(min_length=2, max_length=30, pattern=r"^[A-Za-z][A-Za-z0-9-]+$")
    name: str = Field(min_length=3, max_length=100)
    description: str = Field(default="", max_length=1000)
    kind: Literal["FEATURE", "MODULE"] = "FEATURE"
    owner: str = Field(default="", max_length=120)


class FeatureCoverageResponse(BaseModel):
    required_total: int
    available_required: int
    missing_required: int
    optional_total: int


class FeatureResponse(BaseModel):
    id: str
    project_id: str
    key: str
    name: str
    description: str
    kind: str
    owner: str
    status: str
    documentation_coverage: FeatureCoverageResponse
    created_at: str
    updated_at: str

    @classmethod
    def from_dto(cls, feature: FeatureDto) -> "FeatureResponse":
        return cls(
            id=feature.id,
            project_id=feature.project_id,
            key=feature.key,
            name=feature.name,
            description=feature.description,
            kind=feature.kind,
            owner=feature.owner,
            status=feature.status,
            documentation_coverage=FeatureCoverageResponse(
                required_total=feature.documentation_coverage.required_total,
                available_required=feature.documentation_coverage.available_required,
                missing_required=feature.documentation_coverage.missing_required,
                optional_total=feature.documentation_coverage.optional_total,
            ),
            created_at=feature.created_at,
            updated_at=feature.updated_at,
        )


class FeatureCollectionResponse(BaseModel):
    items: list[FeatureResponse]
    total: int


class DocumentationMapItemResponse(BaseModel):
    document_type: str
    requirement: str
    coverage_status: str
    document_id: str | None
    policy_key: str
    created_at: str
    updated_at: str

    @classmethod
    def from_dto(
        cls,
        item: FeatureDocumentationMapItemDto,
    ) -> "DocumentationMapItemResponse":
        return cls(
            document_type=item.document_type,
            requirement=item.requirement,
            coverage_status=item.coverage_status,
            document_id=item.document_id,
            policy_key=item.policy_key,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )


class DocumentationMapResponse(BaseModel):
    feature_id: str
    policy_key: str
    items: list[DocumentationMapItemResponse]
    total: int


def get_feature_service(request: Request) -> FeatureApplicationService:
    return cast(FeatureApplicationService, request.app.state.feature_service)


FeatureServiceDependency = Annotated[
    FeatureApplicationService,
    Depends(get_feature_service),
]


@router.post("", response_model=FeatureResponse, status_code=status.HTTP_201_CREATED)
async def create_feature(
    workspace_id: str,
    project_id: str,
    payload: CreateFeatureRequest,
    service: FeatureServiceDependency,
) -> FeatureResponse:
    feature = await service.create(
        CreateFeatureCommand(
            workspace_id=workspace_id,
            project_id=project_id,
            key=payload.key,
            name=payload.name,
            description=payload.description,
            kind=payload.kind,
            owner=payload.owner,
        )
    )
    return FeatureResponse.from_dto(feature)


@router.get("", response_model=FeatureCollectionResponse)
async def list_features(
    workspace_id: str,
    project_id: str,
    service: FeatureServiceDependency,
) -> FeatureCollectionResponse:
    features = await service.list_features(workspace_id, project_id)
    items = [FeatureResponse.from_dto(feature) for feature in features]
    return FeatureCollectionResponse(items=items, total=len(items))


@router.get("/{feature_id}", response_model=FeatureResponse)
async def get_feature(
    workspace_id: str,
    project_id: str,
    feature_id: str,
    service: FeatureServiceDependency,
) -> FeatureResponse:
    return FeatureResponse.from_dto(await service.get(workspace_id, project_id, feature_id))


@router.post("/{feature_id}/archive", response_model=FeatureResponse)
async def archive_feature(
    workspace_id: str,
    project_id: str,
    feature_id: str,
    service: FeatureServiceDependency,
) -> FeatureResponse:
    return FeatureResponse.from_dto(await service.archive(workspace_id, project_id, feature_id))


@router.get("/{feature_id}/documentation-map", response_model=DocumentationMapResponse)
async def get_documentation_map(
    workspace_id: str,
    project_id: str,
    feature_id: str,
    service: FeatureServiceDependency,
) -> DocumentationMapResponse:
    items = await service.documentation_map(workspace_id, project_id, feature_id)
    responses = [DocumentationMapItemResponse.from_dto(item) for item in items]
    policy_key = responses[0].policy_key if responses else "feature-documentation-baseline-v1"
    return DocumentationMapResponse(
        feature_id=feature_id,
        policy_key=policy_key,
        items=responses,
        total=len(responses),
    )


_FEATURE_ERROR_STATUS: Mapping[type[FeatureError], int] = {
    InvalidFeatureIdError: 422,
    InvalidFeatureKeyError: 422,
    InvalidFeatureNameError: 422,
    InvalidFeatureDescriptionError: 422,
    InvalidFeatureOwnerError: 422,
    InvalidFeatureProjectIdError: 422,
    InvalidFeatureKindError: 422,
    FeatureKeyAlreadyExistsError: 409,
    FeatureNotFoundError: 404,
    FeatureProjectNotFoundError: 404,
    FeatureWorkspaceMismatchError: 404,
    FeatureProjectArchivedError: 409,
    FeatureAlreadyArchivedError: 409,
}


async def feature_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, FeatureError):
        raise exc
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=_FEATURE_ERROR_STATUS.get(type(exc), 400),
        content={
            "error": {
                "code": exc.code,
                "message": str(exc),
                "request_id": request_id,
            }
        },
    )
