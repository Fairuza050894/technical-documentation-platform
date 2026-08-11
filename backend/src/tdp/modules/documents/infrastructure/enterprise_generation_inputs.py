from datetime import datetime

from tdp.modules.catalog.domain.model import (
    ApiOperation,
    ApiPayload,
    ApiSchema,
    SynchronizationId,
    SynchronizationStatus,
)
from tdp.modules.catalog.domain.repository import CatalogRepository
from tdp.modules.documents.application.enterprise_generation_ports import (
    EnterpriseGenerationContext,
    GenerationClaimFact,
    GenerationEvidenceFact,
    GenerationOperationFact,
    GenerationSchemaFact,
)
from tdp.modules.documents.domain.errors import (
    DocumentProjectArchivedError,
    DocumentProjectNotFoundError,
    InvalidDocumentGenerationError,
)
from tdp.modules.documents.domain.generation import (
    EnterpriseDocumentGenerationProfile,
    GenerationReadinessFinding,
    GenerationReadinessSnapshot,
)
from tdp.modules.evidence.domain.model import Claim, EvidenceArtifact
from tdp.modules.evidence.domain.repository import EvidenceRepository
from tdp.modules.projects.domain.model import Project, ProjectId, ProjectStatus
from tdp.modules.projects.domain.repository import ProjectRepository
from tdp.modules.readiness.application.service import ReadinessApplicationService
from tdp.modules.sources.domain.model import SourceId
from tdp.modules.sources.domain.repository import SourceRepository
from tdp.modules.workspaces.domain.model import WorkspaceId, WorkspaceStatus
from tdp.modules.workspaces.domain.repository import WorkspaceRepository


class RepositoryBackedEnterpriseGenerationInputProvider:
    def __init__(
        self,
        project_repository: ProjectRepository,
        workspace_repository: WorkspaceRepository,
        source_repository: SourceRepository,
        catalog_repository: CatalogRepository,
        evidence_repository: EvidenceRepository,
        readiness_service: ReadinessApplicationService,
    ) -> None:
        self._project_repository = project_repository
        self._workspace_repository = workspace_repository
        self._source_repository = source_repository
        self._catalog_repository = catalog_repository
        self._evidence_repository = evidence_repository
        self._readiness_service = readiness_service

    async def readiness(
        self,
        project_id: str,
        profile: EnterpriseDocumentGenerationProfile,
    ) -> GenerationReadinessSnapshot:
        await self._require_writable_project(project_id)
        assessment = await self._readiness_service.document_readiness(
            project_id,
            profile.document_type.value,
        )
        return GenerationReadinessSnapshot(
            policy_version=assessment.policy_version,
            state=assessment.readiness_state,
            eligible=assessment.eligible,
            findings=tuple(
                GenerationReadinessFinding(
                    rule_code=item.rule_code,
                    severity=item.severity,
                    message=item.message,
                    missing_input=item.missing_input,
                    remediation=item.remediation,
                    supporting_references=tuple(item.supporting_references),
                )
                for item in assessment.findings
            ),
        )

    async def collect(
        self,
        project_id: str,
        profile: EnterpriseDocumentGenerationProfile,
    ) -> EnterpriseGenerationContext:
        project = await self._require_writable_project(project_id)
        readiness = await self.readiness(project_id, profile)
        artifacts = await self._evidence_repository.list_artifacts_by_project(project_id)
        primary_candidates = [
            artifact
            for artifact in artifacts
            if artifact.kind.value == profile.primary_evidence_kind
        ]
        if not primary_candidates:
            raise InvalidDocumentGenerationError(
                f"{profile.display_name} requires {profile.primary_evidence_kind} evidence."
            )
        primary = max(primary_candidates, key=_artifact_sort_key)

        run = await self._catalog_repository.get_run(
            SynchronizationId.from_string(primary.origin_id)
        )
        if run is None or run.project_id != project_id:
            raise InvalidDocumentGenerationError(
                "The selected evidence no longer resolves to a Project synchronization."
            )
        if run.status is not SynchronizationStatus.COMPLETED or run.completed_at is None:
            raise InvalidDocumentGenerationError(
                "Enterprise generation requires a completed synchronization evidence origin."
            )

        source = await self._source_repository.get(SourceId.from_string(run.source_id))
        if source is None:
            raise InvalidDocumentGenerationError(
                "The selected synchronization source could not be resolved."
            )

        operations = await self._catalog_repository.list_operations_by_run(run.id)
        schemas = await self._catalog_repository.list_schemas_by_run(run.id)
        claims = await self._evidence_repository.list_claims_by_project(project_id)
        relevant_claims = tuple(
            sorted(
                (
                    claim
                    for claim in claims
                    if profile.document_type.value in claim.relevant_document_types
                ),
                key=lambda item: (item.classification.value, item.created_at, str(item.id)),
            )
        )
        relevant_evidence = _relevant_evidence(
            artifacts,
            primary,
            relevant_claims,
        )

        return EnterpriseGenerationContext(
            profile=profile,
            readiness=readiness,
            project_id=str(project.id),
            project_key=str(project.key),
            project_name=str(project.name),
            project_description=str(project.description),
            workspace_id=project.workspace_id,
            source_id=str(source.id),
            source_name=str(source.name),
            api_title=source.api_title,
            api_version=source.api_version,
            openapi_version=source.openapi_version,
            target_run_id=str(run.id),
            source_checksum=run.source_checksum,
            snapshot_completed_at=run.completed_at.isoformat(),
            primary_evidence_id=str(primary.id),
            available_snapshot_count=len(primary_candidates),
            evidence=tuple(_evidence_fact(item) for item in relevant_evidence),
            claims=tuple(_claim_fact(item) for item in relevant_claims),
            operations=tuple(_operation_fact(item) for item in operations),
            schemas=tuple(_schema_fact(item) for item in schemas),
        )

    async def _require_writable_project(self, project_id: str) -> Project:
        project = await self._project_repository.get(ProjectId.from_string(project_id))
        if project is None:
            raise DocumentProjectNotFoundError(f"Project {project_id} was not found.")
        if project.status is ProjectStatus.ARCHIVED:
            raise DocumentProjectArchivedError(
                "Enterprise document generation is not allowed for an archived project."
            )

        workspace = await self._workspace_repository.get(
            WorkspaceId.from_string(project.workspace_id)
        )
        if workspace is None:
            raise DocumentProjectNotFoundError(f"Workspace for project {project_id} was not found.")
        if workspace.status is WorkspaceStatus.ARCHIVED:
            raise DocumentProjectArchivedError(
                "Enterprise document generation is not allowed for an archived workspace."
            )
        return project


def _artifact_sort_key(
    artifact: EvidenceArtifact,
) -> tuple[datetime, datetime, str]:
    return (artifact.captured_at, artifact.created_at, str(artifact.id))


def _relevant_evidence(
    artifacts: list[EvidenceArtifact],
    primary: EvidenceArtifact,
    claims: tuple[Claim, ...],
) -> tuple[EvidenceArtifact, ...]:
    by_id = {str(item.id): item for item in artifacts}
    selected: dict[str, EvidenceArtifact] = {str(primary.id): primary}
    for claim in claims:
        for evidence_id in claim.evidence_ids:
            artifact = by_id.get(str(evidence_id))
            if artifact is not None:
                selected[str(artifact.id)] = artifact
    return tuple(sorted(selected.values(), key=lambda item: (item.kind.value, str(item.id))))


def _evidence_fact(artifact: EvidenceArtifact) -> GenerationEvidenceFact:
    return GenerationEvidenceFact(
        id=str(artifact.id),
        kind=artifact.kind.value,
        checksum=str(artifact.checksum),
        source_reference=artifact.source_reference,
        content_reference=artifact.content_reference,
        captured_at=artifact.captured_at.isoformat(),
    )


def _claim_fact(claim: Claim) -> GenerationClaimFact:
    return GenerationClaimFact(
        id=str(claim.id),
        classification=claim.classification.value,
        statement=claim.statement,
        evidence_ids=tuple(str(item) for item in claim.evidence_ids),
        derivation_reference=claim.derivation_reference,
    )


def _operation_fact(operation: ApiOperation) -> GenerationOperationFact:
    return GenerationOperationFact(
        method=operation.method,
        path=operation.path,
        operation_id=operation.operation_id,
        summary=operation.summary,
        description=operation.description,
        tags=operation.tags,
        deprecated=operation.deprecated,
        security_schemes=operation.security_schemes,
        parameters=tuple(
            _parameter_text(
                item.name,
                item.location,
                item.required,
                item.schema_type,
                item.schema_format,
                item.schema_reference,
            )
            for item in operation.parameters
        ),
        request_body=_payload_text(operation.request_body),
        responses=tuple(
            _response_text(
                item.status_code,
                item.description,
                item.media_types,
                item.schema_types,
                item.schema_references,
            )
            for item in operation.responses
        ),
        source_pointer=operation.source_pointer,
    )


def _schema_fact(schema: ApiSchema) -> GenerationSchemaFact:
    return GenerationSchemaFact(
        name=schema.name,
        schema_type=schema.schema_type,
        description=schema.description,
        required_fields=schema.required_fields,
        properties=tuple(
            _property_text(
                item.name,
                item.schema_type,
                item.schema_format,
                item.required,
                item.reference,
            )
            for item in schema.properties
        ),
        source_pointer=schema.source_pointer,
    )


def _parameter_text(
    name: str,
    location: str,
    required: bool,
    schema_type: str,
    schema_format: str,
    schema_reference: str,
) -> str:
    schema = schema_reference or schema_type or "unspecified"
    if schema_format:
        schema = f"{schema} ({schema_format})"
    requirement = "required" if required else "optional"
    return f"{name} — {location}; {requirement}; {schema}"


def _payload_text(payload: ApiPayload | None) -> str:
    if payload is None:
        return "Not defined"
    required = "required" if payload.required else "optional"
    media_types = ", ".join(payload.media_types) or "unspecified"
    schemas = ", ".join(payload.schema_references or payload.schema_types) or "unspecified"
    return f"{required}; media: {media_types}; schemas: {schemas}"


def _response_text(
    status_code: str,
    description: str,
    media_types: tuple[str, ...],
    schema_types: tuple[str, ...],
    schema_references: tuple[str, ...],
) -> str:
    media = ", ".join(media_types) or "unspecified"
    schemas = ", ".join(schema_references or schema_types) or "unspecified"
    summary = description.strip() or "No description"
    return f"{status_code} — {summary}; media: {media}; schemas: {schemas}"


def _property_text(
    name: str,
    schema_type: str,
    schema_format: str,
    required: bool,
    reference: str,
) -> str:
    value_type = reference or schema_type or "unspecified"
    if schema_format:
        value_type = f"{value_type} ({schema_format})"
    requirement = "required" if required else "optional"
    return f"{name} — {value_type}; {requirement}"
