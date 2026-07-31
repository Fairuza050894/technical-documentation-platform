from datetime import UTC, datetime
from uuid import UUID

from tdp.modules.catalog.domain.model import (
    ApiOperation,
    ApiPayload,
    ApiResponse,
    ApiSchema,
    ApiSchemaProperty,
    SynchronizationId,
    SynchronizationRun,
    SynchronizationStatus,
)
from tdp.modules.changes.domain.model import (
    Change,
    ChangeKind,
    ChangeSeverity,
    Comparison,
)
from tdp.modules.documents.application.ports import TechnicalSourceOverviewContext
from tdp.modules.documents.infrastructure.markdown_renderer import (
    DeterministicTechnicalSourceOverviewRenderer,
)
from tdp.modules.projects.domain.model import (
    Project,
    ProjectDescription,
    ProjectId,
    ProjectKey,
    ProjectName,
    ProjectStatus,
    WorkspaceType,
)
from tdp.modules.sources.domain.model import (
    ArtifactKey,
    SourceChecksum,
    SourceConnection,
    SourceFileName,
    SourceId,
    SourceMediaType,
    SourceName,
    SourceProjectId,
    SourceStatus,
    SourceType,
)


def test_renderer_is_deterministic_and_preserves_source_evidence() -> None:
    project_id = "11111111-1111-4111-8111-111111111111"
    source_id = "22222222-2222-4222-8222-222222222222"
    run_id = SynchronizationId(UUID("33333333-3333-4333-8333-333333333333"))
    completed_at = datetime(2026, 7, 29, 7, 0, tzinfo=UTC)

    project = Project(
        id=ProjectId(UUID(project_id)),
        key=ProjectKey("DOCS"),
        name=ProjectName("Documentation Platform"),
        description=ProjectDescription("Commerce platform documentation."),
        workspace_type=WorkspaceType.PERSONAL,
        status=ProjectStatus.ACTIVE,
        created_at=completed_at,
        updated_at=completed_at,
    )
    source = SourceConnection(
        id=SourceId(UUID(source_id)),
        project_id=SourceProjectId(UUID(project_id)),
        name=SourceName("Commerce API v2"),
        source_type=SourceType.OPENAPI_FILE,
        status=SourceStatus.READY,
        original_file_name=SourceFileName("commerce-api-v2.yaml"),
        media_type=SourceMediaType.YAML,
        checksum=SourceChecksum("a" * 64),
        artifact_key=ArtifactKey(f"{source_id}/source.yaml"),
        openapi_version="3.1.0",
        api_title="Commerce API",
        api_version="2.0.0",
        path_count=1,
        operation_count=1,
        created_at=completed_at,
        updated_at=completed_at,
    )
    run = SynchronizationRun(
        id=run_id,
        project_id=project_id,
        source_id=source_id,
        source_checksum="a" * 64,
        status=SynchronizationStatus.COMPLETED,
        operation_count=1,
        schema_count=1,
        error_code="",
        error_message="",
        started_at=completed_at,
        completed_at=completed_at,
    )
    operation = ApiOperation(
        synchronization_id=run_id,
        project_id=project_id,
        source_id=source_id,
        method="POST",
        path="/orders",
        operation_id="createOrder",
        summary="Create an order",
        description="",
        tags=("Orders",),
        deprecated=False,
        security_schemes=("BearerAuth",),
        parameters=(),
        request_body=ApiPayload(
            required=True,
            media_types=("application/json",),
            schema_types=("object",),
            schema_references=("#/components/schemas/CreateOrderRequest",),
        ),
        responses=(
            ApiResponse(
                status_code="201",
                description="Created",
                media_types=("application/json",),
                schema_types=("object",),
                schema_references=("#/components/schemas/Order",),
            ),
        ),
        source_pointer="#/paths/~1orders/post",
    )
    schema = ApiSchema(
        synchronization_id=run_id,
        project_id=project_id,
        source_id=source_id,
        name="CreateOrderRequest",
        schema_type="object",
        description="",
        required_fields=("customerId",),
        properties=(
            ApiSchemaProperty(
                name="customerId",
                schema_type="string",
                schema_format="uuid",
                required=True,
                reference="",
                description="",
            ),
        ),
        source_pointer="#/components/schemas/CreateOrderRequest",
    )
    comparison = Comparison(
        project_id=project_id,
        baseline_run_id="44444444-4444-4444-8444-444444444444",
        target_run_id=str(run_id),
        changes=(
            Change(
                entity_type="SCHEMA",
                entity_key="CreateOrderRequest",
                kind=ChangeKind.MODIFIED,
                severity=ChangeSeverity.BREAKING,
                summary="Schema CreateOrderRequest changed.",
                before_pointer="#/components/schemas/CreateOrderRequest",
                after_pointer="#/components/schemas/CreateOrderRequest",
                details={"new_required_fields": ["customerId"]},
            ),
        ),
    )
    context = TechnicalSourceOverviewContext(
        project=project,
        source=source,
        target_run=run,
        operations=(operation,),
        schemas=(schema,),
        comparison=comparison,
    )

    renderer = DeterministicTechnicalSourceOverviewRenderer()
    first = renderer.render(context)
    second = renderer.render(context)

    assert first == second
    assert "# Technical Source Overview: Commerce API" in first
    assert "`#/paths/~1orders/post`" in first
    assert "`#/components/schemas/CreateOrderRequest`" in first
    assert "Breaking changes: **1**" in first
    assert "| Ownership | Personal |" in first
    assert "| Workspace type |" not in first
    assert "does not use AI" in first
