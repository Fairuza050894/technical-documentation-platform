from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from tdp.config import Settings, get_settings
from tdp.modules.catalog.application.service import CatalogApplicationService
from tdp.modules.catalog.domain.errors import CatalogError
from tdp.modules.catalog.infrastructure.openapi_parser import DeterministicOpenApiCatalogParser
from tdp.modules.catalog.infrastructure.sqlite_repository import SqliteCatalogRepository
from tdp.modules.catalog.presentation.http.router import router as catalog_router
from tdp.modules.changes.application.service import ChangeDetectionApplicationService
from tdp.modules.changes.domain.errors import ChangeDetectionError
from tdp.modules.changes.domain.model import DeterministicCatalogComparator
from tdp.modules.changes.presentation.http.router import router as changes_router
from tdp.modules.documents.application.service import DocumentApplicationService
from tdp.modules.documents.domain.errors import DocumentError
from tdp.modules.documents.infrastructure.markdown_renderer import (
    DeterministicTechnicalSourceOverviewRenderer,
)
from tdp.modules.documents.infrastructure.sqlite_repository import SqliteDocumentRepository
from tdp.modules.documents.presentation.http.router import router as documents_router
from tdp.modules.projects.application.service import ProjectApplicationService
from tdp.modules.projects.domain.errors import ProjectError
from tdp.modules.projects.infrastructure.sqlite_repository import SqliteProjectRepository
from tdp.modules.projects.presentation.http.router import (
    router as projects_router,
)
from tdp.modules.projects.presentation.http.router import (
    workspace_projects_router,
)
from tdp.modules.sources.application.service import SourceApplicationService
from tdp.modules.sources.domain.errors import SourceError
from tdp.modules.sources.infrastructure.local_artifact_store import LocalArtifactStore
from tdp.modules.sources.infrastructure.openapi_inspector import DeterministicOpenApiInspector
from tdp.modules.sources.infrastructure.project_access import RepositoryBackedProjectAccess
from tdp.modules.sources.infrastructure.sqlite_repository import SqliteSourceRepository
from tdp.modules.sources.presentation.http.router import router as sources_router
from tdp.modules.workspaces.application.service import WorkspaceApplicationService
from tdp.modules.workspaces.domain.errors import WorkspaceError
from tdp.modules.workspaces.infrastructure.sqlite_repository import SqliteWorkspaceRepository
from tdp.modules.workspaces.presentation.http.router import router as workspaces_router
from tdp.presentation.http.errors import (
    catalog_error_handler,
    change_detection_error_handler,
    document_error_handler,
    project_error_handler,
    source_error_handler,
    validation_error_handler,
    workspace_error_handler,
)
from tdp.presentation.http.middleware.request_id import RequestIdMiddleware
from tdp.presentation.http.routers.health import router as health_router


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or get_settings()
    workspace_repository = SqliteWorkspaceRepository(runtime_settings.database_path)
    project_repository = SqliteProjectRepository(runtime_settings.database_path)
    source_repository = SqliteSourceRepository(runtime_settings.database_path)
    catalog_repository = SqliteCatalogRepository(runtime_settings.database_path)
    document_repository = SqliteDocumentRepository(runtime_settings.database_path)
    project_access = RepositoryBackedProjectAccess(
        project_repository,
        workspace_repository,
    )
    artifact_store = LocalArtifactStore(runtime_settings.artifact_root_path)

    application = FastAPI(
        title=runtime_settings.app_name,
        version=runtime_settings.app_version,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    application.state.settings = runtime_settings
    application.state.workspace_service = WorkspaceApplicationService(workspace_repository)
    application.state.project_service = ProjectApplicationService(
        project_repository,
        workspace_repository,
    )
    application.state.source_service = SourceApplicationService(
        source_repository,
        project_access,
        DeterministicOpenApiInspector(),
        artifact_store,
        max_file_bytes=runtime_settings.max_source_file_bytes,
    )
    application.state.catalog_service = CatalogApplicationService(
        catalog_repository,
        source_repository,
        project_access,
        artifact_store,
        DeterministicOpenApiCatalogParser(),
    )
    comparator = DeterministicCatalogComparator()
    application.state.change_detection_service = ChangeDetectionApplicationService(
        catalog_repository,
        comparator,
    )
    application.state.document_service = DocumentApplicationService(
        document_repository,
        project_repository,
        source_repository,
        catalog_repository,
        comparator,
        DeterministicTechnicalSourceOverviewRenderer(),
        workspace_repository,
    )
    application.add_middleware(RequestIdMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(runtime_settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )
    application.add_exception_handler(CatalogError, catalog_error_handler)
    application.add_exception_handler(ChangeDetectionError, change_detection_error_handler)
    application.add_exception_handler(DocumentError, document_error_handler)
    application.add_exception_handler(ProjectError, project_error_handler)
    application.add_exception_handler(SourceError, source_error_handler)
    application.add_exception_handler(WorkspaceError, workspace_error_handler)
    application.add_exception_handler(RequestValidationError, validation_error_handler)
    application.include_router(health_router, prefix=runtime_settings.api_prefix)
    application.include_router(workspaces_router, prefix=runtime_settings.api_prefix)
    application.include_router(projects_router, prefix=runtime_settings.api_prefix)
    application.include_router(workspace_projects_router, prefix=runtime_settings.api_prefix)
    application.include_router(sources_router, prefix=runtime_settings.api_prefix)
    application.include_router(catalog_router, prefix=runtime_settings.api_prefix)
    application.include_router(changes_router, prefix=runtime_settings.api_prefix)
    application.include_router(documents_router, prefix=runtime_settings.api_prefix)
    return application


app = create_app()
