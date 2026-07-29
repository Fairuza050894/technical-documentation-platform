from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from tdp.config import Settings, get_settings
from tdp.modules.projects.application.service import ProjectApplicationService
from tdp.modules.projects.domain.errors import ProjectError
from tdp.modules.projects.infrastructure.sqlite_repository import SqliteProjectRepository
from tdp.modules.projects.presentation.http.router import router as projects_router
from tdp.presentation.http.errors import project_error_handler, validation_error_handler
from tdp.presentation.http.middleware.request_id import RequestIdMiddleware
from tdp.presentation.http.routers.health import router as health_router


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or get_settings()
    project_repository = SqliteProjectRepository(runtime_settings.database_path)

    application = FastAPI(
        title=runtime_settings.app_name,
        version=runtime_settings.app_version,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    application.state.settings = runtime_settings
    application.state.project_service = ProjectApplicationService(project_repository)
    application.add_middleware(RequestIdMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(runtime_settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )
    application.add_exception_handler(ProjectError, project_error_handler)
    application.add_exception_handler(RequestValidationError, validation_error_handler)
    application.include_router(health_router, prefix=runtime_settings.api_prefix)
    application.include_router(projects_router, prefix=runtime_settings.api_prefix)
    return application


app = create_app()
