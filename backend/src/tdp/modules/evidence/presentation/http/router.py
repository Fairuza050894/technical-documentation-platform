from collections.abc import Mapping
from dataclasses import asdict
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from tdp.modules.evidence.application.commands import (
    CreateClaimCommand,
    RegisterReferencedEvidenceCommand,
    RegisterSnapshotEvidenceCommand,
    RegisterSourceEvidenceCommand,
)
from tdp.modules.evidence.application.dto import ClaimDto, EvidenceArtifactDto
from tdp.modules.evidence.application.service import EvidenceApplicationService
from tdp.modules.evidence.domain.errors import (
    ClaimNotFoundError,
    EvidenceArtifactNotFoundError,
    EvidenceError,
    EvidenceFeatureArchivedError,
    EvidenceFeatureNotFoundError,
    EvidenceOriginConflictError,
    EvidenceProjectArchivedError,
    EvidenceProjectNotFoundError,
    EvidenceSnapshotNotCompletedError,
    EvidenceSnapshotNotFoundError,
    EvidenceSourceNotFoundError,
    EvidenceWorkspaceArchivedError,
    EvidenceWorkspaceNotFoundError,
    InvalidClaimClassificationError,
    InvalidClaimDerivationError,
    InvalidClaimDocumentTypeError,
    InvalidClaimEvidenceError,
    InvalidClaimIdError,
    InvalidClaimStatementError,
    InvalidEvidenceArtifactIdError,
    InvalidEvidenceCaptureTimeError,
    InvalidEvidenceChecksumError,
    InvalidEvidenceKindError,
    InvalidEvidenceReferenceError,
)
from tdp.presentation.http.dependencies.identity import PrincipalDependency

router = APIRouter(tags=["evidence"])


class RegisterReferencedEvidenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["USER_JOURNEY", "DEPLOYMENT_RUNTIME", "UAT_RESULT"]
    source_reference: str = Field(min_length=3, max_length=500)
    origin_id: str = Field(min_length=1, max_length=200, pattern=r"^\S+$")
    checksum: str = Field(min_length=64, max_length=64, pattern=r"^[A-Fa-f0-9]{64}$")
    content_reference: str = Field(min_length=3, max_length=500)
    captured_at: AwareDatetime
    feature_id: str | None = None


class CreateClaimRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statement: str = Field(min_length=3, max_length=2000)
    classification: Literal["OBSERVED", "INFERRED", "UNVERIFIED"]
    evidence_ids: list[str] = Field(default_factory=list, max_length=100)
    derivation_reference: str = Field(default="", max_length=500)
    relevant_document_types: list[str] = Field(default_factory=list, max_length=10)
    feature_id: str | None = None


class EvidenceArtifactResponse(BaseModel):
    id: str
    workspace_id: str
    project_id: str
    feature_id: str | None
    kind: str
    source_system: str
    source_reference: str
    origin_id: str
    checksum: str
    content_reference: str
    collection_method: str
    collected_by: str
    captured_at: str
    created_at: str

    @classmethod
    def from_dto(cls, artifact: EvidenceArtifactDto) -> "EvidenceArtifactResponse":
        return cls.model_validate(asdict(artifact))


class EvidenceCollectionResponse(BaseModel):
    items: list[EvidenceArtifactResponse]
    total: int


class ClaimResponse(BaseModel):
    id: str
    workspace_id: str
    project_id: str
    feature_id: str | None
    statement: str
    classification: str
    evidence_ids: list[str]
    derivation_reference: str
    relevant_document_types: list[str]
    asserted_by: str
    created_at: str

    @classmethod
    def from_dto(cls, claim: ClaimDto) -> "ClaimResponse":
        return cls.model_validate(asdict(claim))


class ClaimCollectionResponse(BaseModel):
    items: list[ClaimResponse]
    total: int


def get_evidence_service(request: Request) -> EvidenceApplicationService:
    return cast(EvidenceApplicationService, request.app.state.evidence_service)


EvidenceServiceDependency = Annotated[EvidenceApplicationService, Depends(get_evidence_service)]


@router.post(
    "/projects/{project_id}/evidence/source-artifacts/{source_id}",
    response_model=EvidenceArtifactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_source_evidence(
    project_id: str,
    source_id: str,
    service: EvidenceServiceDependency,
    principal: PrincipalDependency,
) -> EvidenceArtifactResponse:
    artifact = await service.register_source_artifact(
        RegisterSourceEvidenceCommand(
            project_id=project_id,
            source_id=source_id,
            principal=principal,
        )
    )
    return EvidenceArtifactResponse.from_dto(artifact)


@router.post(
    "/projects/{project_id}/evidence/catalog-snapshots/{synchronization_id}",
    response_model=EvidenceArtifactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_catalog_snapshot_evidence(
    project_id: str,
    synchronization_id: str,
    service: EvidenceServiceDependency,
    principal: PrincipalDependency,
) -> EvidenceArtifactResponse:
    artifact = await service.register_catalog_snapshot(
        RegisterSnapshotEvidenceCommand(
            project_id=project_id,
            synchronization_id=synchronization_id,
            principal=principal,
        )
    )
    return EvidenceArtifactResponse.from_dto(artifact)


@router.post(
    "/projects/{project_id}/evidence/references",
    response_model=EvidenceArtifactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_referenced_evidence(
    project_id: str,
    payload: RegisterReferencedEvidenceRequest,
    service: EvidenceServiceDependency,
    principal: PrincipalDependency,
) -> EvidenceArtifactResponse:
    artifact = await service.register_referenced_evidence(
        RegisterReferencedEvidenceCommand(
            project_id=project_id,
            kind=payload.kind,
            source_reference=payload.source_reference,
            origin_id=payload.origin_id,
            checksum=payload.checksum,
            content_reference=payload.content_reference,
            captured_at=payload.captured_at,
            feature_id=payload.feature_id,
            principal=principal,
        )
    )
    return EvidenceArtifactResponse.from_dto(artifact)


@router.get(
    "/projects/{project_id}/evidence",
    response_model=EvidenceCollectionResponse,
)
async def list_project_evidence(
    project_id: str,
    service: EvidenceServiceDependency,
) -> EvidenceCollectionResponse:
    artifacts = await service.list_evidence(project_id)
    items = [EvidenceArtifactResponse.from_dto(item) for item in artifacts]
    return EvidenceCollectionResponse(items=items, total=len(items))


@router.get("/evidence/{artifact_id}", response_model=EvidenceArtifactResponse)
async def get_evidence(
    artifact_id: str,
    service: EvidenceServiceDependency,
) -> EvidenceArtifactResponse:
    return EvidenceArtifactResponse.from_dto(await service.get_evidence(artifact_id))


@router.post(
    "/projects/{project_id}/claims",
    response_model=ClaimResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_claim(
    project_id: str,
    payload: CreateClaimRequest,
    service: EvidenceServiceDependency,
    principal: PrincipalDependency,
) -> ClaimResponse:
    claim = await service.create_claim(
        CreateClaimCommand(
            project_id=project_id,
            statement=payload.statement,
            classification=payload.classification,
            evidence_ids=tuple(payload.evidence_ids),
            derivation_reference=payload.derivation_reference,
            relevant_document_types=tuple(payload.relevant_document_types),
            feature_id=payload.feature_id,
            principal=principal,
        )
    )
    return ClaimResponse.from_dto(claim)


@router.get(
    "/projects/{project_id}/claims",
    response_model=ClaimCollectionResponse,
)
async def list_project_claims(
    project_id: str,
    service: EvidenceServiceDependency,
) -> ClaimCollectionResponse:
    claims = await service.list_claims(project_id)
    items = [ClaimResponse.from_dto(item) for item in claims]
    return ClaimCollectionResponse(items=items, total=len(items))


@router.get("/claims/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: str,
    service: EvidenceServiceDependency,
) -> ClaimResponse:
    return ClaimResponse.from_dto(await service.get_claim(claim_id))


_EVIDENCE_ERROR_STATUS: Mapping[type[EvidenceError], int] = {
    InvalidEvidenceArtifactIdError: 422,
    InvalidEvidenceCaptureTimeError: 422,
    InvalidEvidenceChecksumError: 422,
    InvalidEvidenceKindError: 422,
    InvalidEvidenceReferenceError: 422,
    InvalidClaimIdError: 422,
    InvalidClaimStatementError: 422,
    InvalidClaimClassificationError: 422,
    InvalidClaimEvidenceError: 422,
    InvalidClaimDerivationError: 422,
    InvalidClaimDocumentTypeError: 422,
    EvidenceArtifactNotFoundError: 404,
    EvidenceProjectNotFoundError: 404,
    EvidenceWorkspaceNotFoundError: 404,
    EvidenceSourceNotFoundError: 404,
    EvidenceSnapshotNotFoundError: 404,
    EvidenceFeatureNotFoundError: 404,
    ClaimNotFoundError: 404,
    EvidenceOriginConflictError: 409,
    EvidenceProjectArchivedError: 409,
    EvidenceWorkspaceArchivedError: 409,
    EvidenceFeatureArchivedError: 409,
    EvidenceSnapshotNotCompletedError: 409,
}


async def evidence_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, EvidenceError):
        raise exc
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=_EVIDENCE_ERROR_STATUS.get(type(exc), 400),
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
