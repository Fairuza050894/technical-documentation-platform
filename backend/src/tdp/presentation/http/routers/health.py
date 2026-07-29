from typing import Literal, cast

from fastapi import APIRouter, Request
from pydantic import BaseModel

from tdp.config import Settings

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
    environment: str


@router.get("/health", response_model=HealthResponse)
async def get_health(request: Request) -> HealthResponse:
    settings = cast(Settings, request.app.state.settings)
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )
