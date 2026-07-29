from dataclasses import asdict
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from tdp.modules.changes.application.dto import ComparisonDto
from tdp.modules.changes.application.service import ChangeDetectionApplicationService

router = APIRouter(tags=["changes"])


class CompareRequest(BaseModel):
    baseline_run_id: str
    target_run_id: str


class ComparisonResponse(BaseModel):
    project_id: str
    baseline_run_id: str
    target_run_id: str
    total: int
    breaking_total: int
    changes: list[dict[str, Any]]

    @classmethod
    def from_dto(cls, comparison: ComparisonDto) -> "ComparisonResponse":
        return cls.model_validate(asdict(comparison))


def get_service(request: Request) -> ChangeDetectionApplicationService:
    return cast(ChangeDetectionApplicationService, request.app.state.change_detection_service)


ServiceDependency = Annotated[ChangeDetectionApplicationService, Depends(get_service)]


@router.post("/projects/{project_id}/comparisons", response_model=ComparisonResponse)
async def compare_snapshots(
    project_id: str,
    payload: CompareRequest,
    service: ServiceDependency,
) -> ComparisonResponse:
    return ComparisonResponse.from_dto(
        await service.compare(project_id, payload.baseline_run_id, payload.target_run_id)
    )
