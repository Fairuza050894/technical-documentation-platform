from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from tdp.config import Settings, get_settings
from tdp.identity.model import IdentityAssurance, RequestPrincipal
from tdp.identity.provider import LocalIdentityProvider
from tdp.modules.catalog.application.service import CatalogApplicationService
from tdp.modules.catalog.domain.errors import CatalogError
from tdp.modules.catalog.infrastructure.openapi_parser import DeterministicOpenApiCatalogParser
from tdp.modules.catalog.infrastructure.sqlite_repository import SqliteCatalogRepository
from tdp.modules.catalog.presentation.http.router import router as catalog_router
from tdp.modules.changes.application.service import ChangeDetectionApplicationService
from tdp.modules.changes.domain.errors import ChangeDetectionError
from tdp.modules.changes.domain.model import DeterministicCatalogComparator
from tdp.modules.changes.presentation.http.router import router as changes_router
from tdp.modules.documents.application.enterprise_generation_service import (
    EnterpriseDocumentGenerationService,
)
from tdp.modules.documents.application.governance_service import (
    DocumentGovernanceApplicationService,
)
from tdp.modules.documents.application.service import DocumentApplicationService
from tdp.modules.documents.domain.errors import (
    DocumentError,
    EnterpriseDocumentGenerationBlockedError,
)
from tdp.modules.documents.infrastructure.enterprise_generation_inputs import (
    RepositoryBackedEnterpriseGenerationInputProvider,
)
from tdp.modules.documents.infrastructure.enterprise_markdown_renderer import (
    DeterministicEnterpriseMarkdownRenderer,
)
from tdp.modules.documents.infrastructure.markdown_renderer import (
    DeterministicTechnicalSourceOverviewRenderer,
)
from tdp.modules.documents.infrastructure.sqlite_repository import SqliteDocumentRepository
from tdp.modules.documents.presentation.http.router import (
    enterprise_generation_blocked_handler,
)
from tdp.modules.documents.presentation.http.router import router as documents_router
from tdp.modules.evidence.application.service import EvidenceApplicationService
from tdp.modules.templates.application.service import TemplateApplicationService
from tdp.modules.scanner.application.service import ScannerApplicationService
from tdp.modules.scanner.infrastructure.sqlite_repository import SqliteScanRepository
from tdp.modules.scanner.infrastructure.document_builder import DocumentStore
from tdp.modules.scanner.presentation.http.router import router as scanner_router
from tdp.modules.scanner.presentation.http.dashboard_router import router as dashboard_router
from tdp.modules.scanner.presentation.http.webhook_router import router as webhook_router
from tdp.modules.scanner.presentation.http.webhook_router import webhook_signature_error_handler, webhook_not_found_handler
from tdp.modules.scanner.application.webhook_service import WebhookApplicationService, WebhookSignatureError, WebhookEventNotFoundError
from tdp.modules.scanner.infrastructure.webhook_repository import SqliteWebhookRepository
from tdp.modules.scanner.presentation.http.router import scanner_error_handler
from tdp.modules.scanner.domain.errors import ScannerError
from tdp.modules.templates.infrastructure.sqlite_repository import SqliteTemplateRepository
from tdp.modules.templates.infrastructure.seed import seed_builtin_templates
from tdp.modules.templates.presentation.http.router import router as templates_router
from tdp.modules.templates.presentation.http.router import template_error_handler
from tdp.modules.templates.domain.errors import TemplateError
from tdp.modules.evidence.domain.errors import EvidenceError
from tdp.modules.evidence.infrastructure.sqlite_repository import SqliteEvidenceRepository
from tdp.modules.evidence.presentation.http.router import (
    evidence_error_handler,
)
from tdp.modules.evidence.presentation.http.router import (
    router as evidence_router,
)
from tdp.modules.features.application.service import FeatureApplicationService
from tdp.modules.features.domain.errors import FeatureError
from tdp.modules.features.infrastructure.sqlite_repository import SqliteFeatureRepository
from tdp.modules.features.presentation.http.router import (
    feature_error_handler,
)
from tdp.modules.features.presentation.http.router import (
    router as features_router,
)
from tdp.modules.projects.application.service import ProjectApplicationService
from tdp.modules.projects.domain.errors import ProjectError
from tdp.modules.projects.infrastructure.sqlite_repository import SqliteProjectRepository
from tdp.modules.projects.presentation.http.router import (
    router as projects_router,
)
from tdp.modules.projects.presentation.http.router import (
    workspace_projects_router,
)
from tdp.modules.readiness.application.service import ReadinessApplicationService
from tdp.modules.readiness.domain.errors import ReadinessError
from tdp.modules.readiness.presentation.http.router import (
    readiness_error_handler,
)
from tdp.modules.readiness.presentation.http.router import (
    router as readiness_router,
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
from tdp.audit.logger import StructuredAuditLogger
from tdp.audit.middleware import AuditMiddleware
from tdp.audit.store import AuditStore
from tdp.presentation.http.middleware.rate_limiting import RateLimitMiddleware
from tdp.presentation.http.middleware.request_id import RequestIdMiddleware
from tdp.presentation.http.middleware.security_headers import SecurityHeadersMiddleware
from tdp.presentation.http.middleware.csrf import CsrfProtectionMiddleware
from tdp.presentation.http.middleware.jwt_auth import JwtAuthMiddleware
from tdp.presentation.http.routers.health import router as health_router
from tdp.presentation.http.routers.identity import router as identity_router
from tdp.presentation.http.routers.audit_logs import router as audit_logs_router
from tdp.presentation.http.routers.auth import router as auth_router
from tdp.identity.oidc import OidcDiscovery
from tdp.identity.jwt_service import JwtService
from tdp.identity.session_store import TokenBlacklist
from tdp.authorization.errors import PermissionDeniedError, permission_denied_handler
from tdp.authorization.policy import AuthorizationPolicy
from tdp.modules.workspaces.infrastructure.membership_repository import SqliteMembershipRepository


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or get_settings()

    # ═══ Identity Provider ═══
    identity_provider = LocalIdentityProvider(
        RequestPrincipal(
            subject_id=runtime_settings.local_identity_subject,
            display_name=runtime_settings.local_identity_name,
            email=runtime_settings.local_identity_email,
            provider="local",
            assurance=IdentityAssurance.DEVELOPMENT,
        )
    )

    # ═══ OIDC + JWT (only when auth_mode == "oidc") ═══
    oidc_discovery: OidcDiscovery | None = None
    jwt_service: JwtService | None = None

    if runtime_settings.auth_mode == "oidc":
        oidc_discovery = OidcDiscovery(
            issuer=runtime_settings.oidc_issuer,
            client_id=runtime_settings.oidc_client_id,
            client_secret=runtime_settings.oidc_client_secret,
        )
        jwt_service = JwtService(
            oidc_discovery=oidc_discovery,
            audience=runtime_settings.oidc_audience or None,
        )

    # ═══ Token blacklist ═══
    token_blacklist = TokenBlacklist(runtime_settings.database_path)

    # ═══ Repositories ═══
    workspace_repository = SqliteWorkspaceRepository(runtime_settings.database_path)
    project_repository = SqliteProjectRepository(runtime_settings.database_path)
    source_repository = SqliteSourceRepository(runtime_settings.database_path)
    catalog_repository = SqliteCatalogRepository(runtime_settings.database_path)
    document_repository = SqliteDocumentRepository(runtime_settings.database_path)
    feature_repository = SqliteFeatureRepository(runtime_settings.database_path)
    evidence_repository = SqliteEvidenceRepository(runtime_settings.database_path)
    template_repository = SqliteTemplateRepository(runtime_settings.database_path)
    scan_repository = SqliteScanRepository(runtime_settings.database_path)
    project_access = RepositoryBackedProjectAccess(
        project_repository,
        workspace_repository,
    )
    artifact_store = LocalArtifactStore(runtime_settings.artifact_root_path)

    # ═══ Application ═══
    application = FastAPI(
        title=runtime_settings.app_name,
        version=runtime_settings.app_version,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    application.state.settings = runtime_settings
    application.state.identity_provider = identity_provider
    application.state.jwt_service = jwt_service
    application.state.token_blacklist = token_blacklist
    application.state.workspace_service = WorkspaceApplicationService(workspace_repository)
    application.state.feature_service = FeatureApplicationService(
        feature_repository,
        project_repository,
        workspace_repository,
    )
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
    application.state.evidence_service = EvidenceApplicationService(
        evidence_repository,
        project_repository,
        workspace_repository,
        feature_repository,
        source_repository,
        catalog_repository,
    )
    readiness_service = ReadinessApplicationService(
        project_repository,
        evidence_repository,
        document_repository,
    )
    application.state.readiness_service = readiness_service
    application.state.enterprise_generation_service = EnterpriseDocumentGenerationService(
        document_repository,
        RepositoryBackedEnterpriseGenerationInputProvider(
            project_repository,
            workspace_repository,
            source_repository,
            catalog_repository,
            evidence_repository,
            readiness_service,
        ),
        DeterministicEnterpriseMarkdownRenderer(),
    )
    application.state.template_service = TemplateApplicationService(template_repository)
    application.state.scanner_service = ScannerApplicationService(scan_repository)
    webhook_repository = SqliteWebhookRepository(runtime_settings.database_path)
    application.state.webhook_service = WebhookApplicationService(
        webhook_repository=webhook_repository,
        scanner_service=application.state.scanner_service,
        webhook_secret="",
    )
    application.state.document_store = DocumentStore(runtime_settings.database_path)

    @application.on_event("startup")
    async def _seed_templates() -> None:
        count = await seed_builtin_templates(template_repository)
        if count > 0:
            print(f"Seeded {count} built-in document templates.")
    application.state.document_governance_service = DocumentGovernanceApplicationService(
        document_repository,
        project_repository,
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

    # --- Authorization (WS 1.2) ---
    membership_repository = SqliteMembershipRepository(runtime_settings.database_path)
    authorization_policy = AuthorizationPolicy(
        membership_lookup=membership_repository,
        default_admin_subjects=runtime_settings.default_admin_subjects,
    )
    application.state.membership_repository = membership_repository
    application.state.authorization_policy = authorization_policy

    # --- Audit ---
    audit_store = AuditStore(runtime_settings.database_path)
    application.state.audit_store = audit_store

    audit_logger = StructuredAuditLogger(
        enabled=runtime_settings.audit_enabled,
        store=audit_store,
    )
    application.state.audit_logger = audit_logger

    # ═══ Middleware (last added = runs first on request) ═══

    # Security headers + HSTS + CSP (outermost)
    application.add_middleware(
        SecurityHeadersMiddleware,
        environment=runtime_settings.environment,
        hsts_max_age=runtime_settings.hsts_max_age,
        hsts_include_subdomains=runtime_settings.hsts_include_subdomains,
        hsts_preload=runtime_settings.hsts_preload,
    )

    # Audit logging
    application.add_middleware(AuditMiddleware, audit_logger=audit_logger)

    # CSRF protection
    application.add_middleware(
        CsrfProtectionMiddleware,
        enabled=runtime_settings.csrf_enabled,
        cookie_secure=runtime_settings.csrf_cookie_secure,
        cookie_samesite=runtime_settings.csrf_cookie_samesite,
    )

    # JWT authentication (OIDC mode only)
    if runtime_settings.auth_mode == "oidc" and jwt_service is not None:
        application.add_middleware(
            JwtAuthMiddleware,
            jwt_service=jwt_service,
            token_blacklist=token_blacklist,
            auth_mode=runtime_settings.auth_mode,
        )

    # Rate limiting
    if runtime_settings.rate_limit_enabled:
        application.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=runtime_settings.rate_limit_requests_per_minute,
        )

    # Request ID
    application.add_middleware(RequestIdMiddleware)

    # CORS (innermost)
    cors_allow_credentials = runtime_settings.csrf_enabled or runtime_settings.auth_mode == "oidc"
    cors_allow_headers = ["Content-Type", "X-Request-ID"]
    if runtime_settings.csrf_enabled:
        cors_allow_headers.append("X-CSrf-Token")
    if runtime_settings.auth_mode == "oidc":
        cors_allow_headers.append("Authorization")

    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(runtime_settings.allowed_origins),
        allow_credentials=cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=cors_allow_headers,
    )

    # ═══ Exception handlers ═══
    application.add_exception_handler(CatalogError, catalog_error_handler)
    application.add_exception_handler(ChangeDetectionError, change_detection_error_handler)
    application.add_exception_handler(DocumentError, document_error_handler)
    application.add_exception_handler(
        EnterpriseDocumentGenerationBlockedError,
        enterprise_generation_blocked_handler,
    )
    application.add_exception_handler(EvidenceError, evidence_error_handler)
    application.add_exception_handler(TemplateError, template_error_handler)
    application.add_exception_handler(ScannerError, scanner_error_handler)
    application.add_exception_handler(WebhookSignatureError, webhook_signature_error_handler)
    application.add_exception_handler(WebhookEventNotFoundError, webhook_not_found_handler)
    application.add_exception_handler(FeatureError, feature_error_handler)
    application.add_exception_handler(ProjectError, project_error_handler)
    application.add_exception_handler(ReadinessError, readiness_error_handler)
    application.add_exception_handler(SourceError, source_error_handler)
    application.add_exception_handler(WorkspaceError, workspace_error_handler)
    application.add_exception_handler(RequestValidationError, validation_error_handler)
    application.add_exception_handler(PermissionDeniedError, permission_denied_handler)

    # ═══ Routers ═══
    application.include_router(health_router, prefix=runtime_settings.api_prefix)
    application.include_router(identity_router, prefix=runtime_settings.api_prefix)
    application.include_router(auth_router, prefix=runtime_settings.api_prefix)
    application.include_router(workspaces_router, prefix=runtime_settings.api_prefix)
    application.include_router(projects_router, prefix=runtime_settings.api_prefix)
    application.include_router(readiness_router, prefix=runtime_settings.api_prefix)
    application.include_router(workspace_projects_router, prefix=runtime_settings.api_prefix)
    application.include_router(features_router, prefix=runtime_settings.api_prefix)
    application.include_router(sources_router, prefix=runtime_settings.api_prefix)
    application.include_router(catalog_router, prefix=runtime_settings.api_prefix)
    application.include_router(changes_router, prefix=runtime_settings.api_prefix)
    application.include_router(evidence_router, prefix=runtime_settings.api_prefix)
    application.include_router(documents_router, prefix=runtime_settings.api_prefix)
    application.include_router(templates_router, prefix=runtime_settings.api_prefix)
    application.include_router(scanner_router, prefix=runtime_settings.api_prefix)
    application.include_router(dashboard_router, prefix=runtime_settings.api_prefix)
    application.include_router(webhook_router, prefix=runtime_settings.api_prefix)
    application.include_router(audit_logs_router, prefix=runtime_settings.api_prefix)

    return application


app = create_app()