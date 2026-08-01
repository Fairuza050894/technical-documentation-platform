import os
import sqlite3
from pathlib import Path
from typing import Literal, cast

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel

from tdp.config import Settings

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
    environment: str


class DependencyStatus(BaseModel):
    status: Literal["ready", "unready"]
    detail: str


class ReadinessResponse(BaseModel):
    status: Literal["ready", "unready"]
    service: str
    version: str
    environment: str
    dependencies: dict[str, DependencyStatus]


@router.get("/health", response_model=HealthResponse)
@router.get("/health/live", response_model=HealthResponse)
async def get_health(request: Request) -> HealthResponse:
    settings = cast(Settings, request.app.state.settings)
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/health/ready", response_model=ReadinessResponse)
async def get_readiness(request: Request, response: Response) -> ReadinessResponse:
    settings = cast(Settings, request.app.state.settings)
    dependencies = {
        "database": _database_status(settings.database_path),
        "artifact_store": _directory_status(settings.artifact_root_path),
    }
    ready = all(item.status == "ready" for item in dependencies.values())
    readiness_status: Literal["ready", "unready"] = "ready" if ready else "unready"
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        status=readiness_status,
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        dependencies=dependencies,
    )


def _database_status(database_path: Path) -> DependencyStatus:
    try:
        with sqlite3.connect(database_path, timeout=1) as connection:
            connection.execute("SELECT 1").fetchone()
    except (OSError, sqlite3.Error) as exc:
        return DependencyStatus(
            status="unready",
            detail=f"SQLite unavailable: {type(exc).__name__}",
        )
    return DependencyStatus(status="ready", detail="SQLite connection succeeded.")


def _directory_status(directory: Path) -> DependencyStatus:
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return DependencyStatus(
            status="unready",
            detail=f"Artifact directory unavailable: {type(exc).__name__}",
        )
    if not os.access(directory, os.R_OK | os.W_OK | os.X_OK):
        return DependencyStatus(status="unready", detail="Artifact directory is not writable.")
    return DependencyStatus(status="ready", detail="Artifact directory is readable and writable.")
