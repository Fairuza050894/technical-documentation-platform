from fastapi import FastAPI

from tdp.modules.catalog.infrastructure.sqlite_repository import SqliteCatalogRepository
from tdp.modules.documents.infrastructure.sqlite_repository import SqliteDocumentRepository
from tdp.modules.evidence.application.scanner_adapter import ScannerEvidenceApplicationService
from tdp.modules.evidence.infrastructure.sqlite_repository import SqliteEvidenceRepository
from tdp.modules.features.infrastructure.sqlite_repository import SqliteFeatureRepository
from tdp.modules.projects.infrastructure.sqlite_repository import SqliteProjectRepository
from tdp.modules.requirements.application.service import RequirementApplicationService
from tdp.modules.requirements.infrastructure.sqlite_repository import SqliteRequirementRepository
from tdp.modules.scanner.infrastructure.sqlite_repository import SqliteScanRepository
from tdp.modules.workflow.application.service import WorkflowApplicationService
from tdp.modules.workflow.infrastructure.sqlite_repository import SqliteWorkflowRepository
from tdp.modules.workspaces.infrastructure.sqlite_repository import SqliteWorkspaceRepository


def ensure_enterprise_core_services(application: FastAPI) -> None:
    """Install Phase 1-5 services lazily without duplicating application bootstrap policy.

    The app factory owns runtime settings. This helper uses the same configured database path and
    creates idempotent SQLite adapters only when the enterprise-core routes are first exercised.
    A later production persistence phase can replace these adapters without changing the domain API.
    """
    if hasattr(application.state, "requirement_service"):
        return

    database_path = application.state.settings.database_path
    workspace_repository = SqliteWorkspaceRepository(database_path)
    project_repository = SqliteProjectRepository(database_path)
    feature_repository = SqliteFeatureRepository(database_path)
    evidence_repository = SqliteEvidenceRepository(database_path)
    document_repository = SqliteDocumentRepository(database_path)
    catalog_repository = SqliteCatalogRepository(database_path)
    requirement_repository = SqliteRequirementRepository(database_path)
    workflow_repository = SqliteWorkflowRepository(database_path)
    scan_repository = SqliteScanRepository(str(database_path))

    application.state.requirement_service = RequirementApplicationService(
        requirement_repository,
        project_repository,
        workspace_repository,
        feature_repository,
        evidence_repository,
        document_repository,
    )
    application.state.workflow_service = WorkflowApplicationService(
        workflow_repository,
        project_repository,
        workspace_repository,
        requirement_repository,
        document_repository,
        catalog_repository,
    )
    application.state.scanner_evidence_service = ScannerEvidenceApplicationService(
        evidence_repository,
        scan_repository,
        project_repository,
        workspace_repository,
        feature_repository,
    )
