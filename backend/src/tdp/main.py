from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from tdp.config import Settings, get_settings
from tdp.modules.projects.application.service import ProjectApplicationService
from tdp.modules.projects.domain.errors import ProjectError
from tdp.modules.projects.infrastructure.sqlite_repository import SqliteProjectRepository
from tdp.modules.projects.presentation.http.router import router as projects_router
from tdp.modules.sources.application.service import SourceApplicationService
from tdp.modules.sources.domain.errors import SourceError
from tdp.modules.sources.infrastructure.local_artifact_store import LocalArtifactStore
from tdp.modules.sources.infrastructure.openapi_inspector import DeterministicOpenApiInspector
from tdp.modules.sources.infrastructure.project_access import RepositoryBackedProjectAccess
from tdp.modules.sources.infrastructure.sqlite_repository import SqliteSourceRepository
from tdp.modules.sources.presentation.http.router import router as sources_router
from tdp.presentation.http.errors import (
    project_error_handler,
    source_error_handler,
    validation_error_handler,
)
from tdp.presentation.http.middleware.request_id import RequestIdMiddleware
from tdp.presentation.http.routers.health import router as health_router


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or get_settings()
    project_repository = SqliteProjectRepository(runtime_settings.database_path)
    source_repository = SqliteSourceRepository(runtime_settings.database_path)

    application = FastAPI(
        title=runtime_settings.app_name,
        version=runtime_settings.app_version,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    application.state.settings = runtime_settings
    application.state.project_service = ProjectApplicationService(project_repository)
    application.state.source_service = SourceApplicationService(
        source_repository,
        RepositoryBackedProjectAccess(project_repository),
        DeterministicOpenApiInspector(),
        LocalArtifactStore(runtime_settings.artifact_root_path),
        max_file_bytes=runtime_settings.max_source_file_bytes,
    )
    application.add_middleware(RequestIdMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(runtime_settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )
    application.add_exception_handler(ProjectError, project_error_handler)
    application.add_exception_handler(SourceError, source_error_handler)
    application.add_exception_handler(RequestValidationError, validation_error_handler)
    application.include_router(health_router, prefix=runtime_settings.api_prefix)
    application.include_router(projects_router, prefix=runtime_settings.api_prefix)
    application.include_router(sources_router, prefix=runtime_settings.api_prefix)
    return application


app = create_app()
