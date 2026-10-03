from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel

from tdp.modules.evidence.application.scanner_adapter import ScannerEvidenceApplicationService
from tdp.modules.evidence.presentation.http.router import (
    EvidenceArtifactResponse,
    EvidenceCollectionResponse,
)
from tdp.presentation.http.dependencies.identity import PrincipalDependency

router = APIRouter(tags=["evidence"])


class RegisterScannerEvidenceRequest(BaseModel):
    feature_id: str | None = None


def get_service(request: Request) -> ScannerEvidenceApplicationService:
    return cast(ScannerEvidenceApplicationService, request.app.state.scanner_evidence_service)


ServiceDependency = Annotated[ScannerEvidenceApplicationService, Depends(get_service)]


@router.post(
    "/projects/{project_id}/evidence/repository-scans/{scan_id}",
    response_model=EvidenceCollectionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_repository_scan_evidence(
    project_id: str,
    scan_id: str,
    payload: RegisterScannerEvidenceRequest,
    service: ServiceDependency,
    principal: PrincipalDependency,
) -> EvidenceCollectionResponse:
    artifacts = await service.register(
        project_id=project_id,
        scan_id=scan_id,
        feature_id=payload.feature_id,
        principal=principal,
    )
    items = [EvidenceArtifactResponse.from_dto(item) for item in artifacts]
    return EvidenceCollectionResponse(items=items, total=len(items))
