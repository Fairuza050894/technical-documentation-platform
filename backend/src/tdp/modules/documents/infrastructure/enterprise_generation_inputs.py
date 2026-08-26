import json
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
    GenerationDeploymentRuntimeFact,
    GenerationDeploymentStepFact,
    GenerationEvidenceFact,
    GenerationJourneyStepFact,
    GenerationOperationFact,
    GenerationRuntimeComponentFact,
    GenerationSchemaFact,
    GenerationUatResultFact,
    GenerationUatScenarioFact,
    GenerationUserJourneyFact,
    GenerationVerificationCheckFact,
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
from tdp.modules.evidence.domain.errors import InvalidEvidenceManifestError
from tdp.modules.evidence.domain.materialization import (
    SEMANTIC_EVIDENCE_MANIFEST_SCHEMA_VERSION,
    EvidenceMaterialization,
    canonicalize_semantic_evidence_manifest,
)
from tdp.modules.evidence.domain.model import Claim, EvidenceArtifact, EvidenceKind
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
        accepted_evidence_kinds = set(profile.accepted_evidence_kinds)
        if accepted_evidence_kinds & _SEMANTIC_EVIDENCE_KIND_VALUES:
            return await self._collect_semantic_context(
                project,
                readiness,
                artifacts,
                profile,
            )

        primary_candidates = [
            artifact for artifact in artifacts if artifact.kind.value in accepted_evidence_kinds
        ]
        if not primary_candidates:
            accepted = ", ".join(profile.accepted_evidence_kinds)
            raise InvalidDocumentGenerationError(
                f"{profile.display_name} requires one of these evidence kinds: {accepted}."
            )
        primary = max(primary_candidates, key=_artifact_sort_key)

        if primary.kind is EvidenceKind.CATALOG_SNAPSHOT:
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
            if source is None or str(source.project_id) != project_id:
                raise InvalidDocumentGenerationError(
                    "The selected synchronization source could not be resolved for this Project."
                )

            operations = await self._catalog_repository.list_operations_by_run(run.id)
            schemas = await self._catalog_repository.list_schemas_by_run(run.id)
            target_run_id: str | None = str(run.id)
            source_checksum = run.source_checksum
            snapshot_completed_at: str | None = run.completed_at.isoformat()
        elif primary.kind is EvidenceKind.SOURCE_ARTIFACT:
            source = await self._source_repository.get(SourceId.from_string(primary.origin_id))
            if source is None or str(source.project_id) != project_id:
                raise InvalidDocumentGenerationError(
                    "The selected source evidence could not be resolved for this Project."
                )

            operations = []
            schemas = []
            target_run_id = None
            source_checksum = str(source.checksum)
            snapshot_completed_at = None
        else:
            raise InvalidDocumentGenerationError(
                f"Unsupported enterprise generation evidence kind: {primary.kind.value}."
            )
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
            target_run_id=target_run_id,
            source_checksum=source_checksum,
            snapshot_completed_at=snapshot_completed_at,
            primary_evidence_id=str(primary.id),
            primary_evidence_kind=primary.kind.value,
            available_snapshot_count=sum(
                artifact.kind is EvidenceKind.CATALOG_SNAPSHOT for artifact in artifacts
            ),
            evidence=tuple(_evidence_fact(item) for item in relevant_evidence),
            claims=tuple(_claim_fact(item) for item in relevant_claims),
            operations=tuple(_operation_fact(item) for item in operations),
            schemas=tuple(_schema_fact(item) for item in schemas),
        )

    async def _collect_semantic_context(
        self,
        project: Project,
        readiness: GenerationReadinessSnapshot,
        artifacts: list[EvidenceArtifact],
        profile: EnterpriseDocumentGenerationProfile,
    ) -> EnterpriseGenerationContext:
        project_id = str(project.id)
        materializations = await self._evidence_repository.list_materializations_by_project(
            project_id
        )
        materialization_by_evidence = {str(item.evidence_id): item for item in materializations}
        accepted_evidence_kinds = set(profile.accepted_evidence_kinds)
        candidates = [
            artifact
            for artifact in artifacts
            if artifact.kind.value in accepted_evidence_kinds
            and _matching_materialization(
                artifact,
                materialization_by_evidence.get(str(artifact.id)),
                project_id,
            )
        ]
        if not candidates:
            raise InvalidDocumentGenerationError(
                f"{profile.display_name} requires materialized governed semantic evidence."
            )

        primary = max(candidates, key=_artifact_sort_key)
        materialization = materialization_by_evidence[str(primary.id)]
        payload = _semantic_payload(primary, materialization)

        user_journey: GenerationUserJourneyFact | None = None
        deployment_runtime: GenerationDeploymentRuntimeFact | None = None
        uat_result: GenerationUatResultFact | None = None
        if primary.kind is EvidenceKind.USER_JOURNEY:
            user_journey = _user_journey_fact(payload)
        elif primary.kind is EvidenceKind.DEPLOYMENT_RUNTIME:
            deployment_runtime = _deployment_runtime_fact(payload)
        elif primary.kind is EvidenceKind.UAT_RESULT:
            uat_result = _uat_result_fact(payload)
        else:
            raise InvalidDocumentGenerationError(
                f"Unsupported semantic evidence kind: {primary.kind.value}."
            )

        return EnterpriseGenerationContext(
            profile=profile,
            readiness=readiness,
            project_id=project_id,
            project_key=str(project.key),
            project_name=str(project.name),
            project_description=str(project.description),
            workspace_id=project.workspace_id,
            source_id=None,
            source_name="Not applicable — semantic evidence",
            api_title="",
            api_version="",
            openapi_version="",
            target_run_id=None,
            source_checksum=str(primary.checksum),
            snapshot_completed_at=None,
            primary_evidence_id=str(primary.id),
            primary_evidence_kind=primary.kind.value,
            available_snapshot_count=sum(
                artifact.kind is EvidenceKind.CATALOG_SNAPSHOT for artifact in artifacts
            ),
            evidence=(_evidence_fact(primary),),
            claims=(),
            operations=(),
            schemas=(),
            user_journey=user_journey,
            deployment_runtime=deployment_runtime,
            uat_result=uat_result,
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


_SEMANTIC_EVIDENCE_KIND_VALUES = {
    EvidenceKind.USER_JOURNEY.value,
    EvidenceKind.DEPLOYMENT_RUNTIME.value,
    EvidenceKind.UAT_RESULT.value,
}


def _matching_materialization(
    artifact: EvidenceArtifact,
    materialization: EvidenceMaterialization | None,
    project_id: str,
) -> bool:
    return (
        materialization is not None
        and materialization.project_id == project_id
        and materialization.kind is artifact.kind
        and str(materialization.checksum) == str(artifact.checksum)
    )


def _semantic_payload(
    artifact: EvidenceArtifact,
    materialization: EvidenceMaterialization,
) -> dict[str, object]:
    try:
        decoded = json.loads(materialization.canonical_manifest)
        if not isinstance(decoded, dict) or not all(isinstance(key, str) for key in decoded):
            raise InvalidDocumentGenerationError(
                "Materialized semantic evidence must contain a canonical object."
            )
        canonical = canonicalize_semantic_evidence_manifest(
            artifact.kind,
            decoded,
        )
    except (json.JSONDecodeError, InvalidEvidenceManifestError) as exc:
        raise InvalidDocumentGenerationError(
            "Materialized semantic evidence could not be validated for generation."
        ) from exc

    if (
        canonical.schema_version != SEMANTIC_EVIDENCE_MANIFEST_SCHEMA_VERSION
        or canonical.canonical_json != materialization.canonical_manifest
        or str(canonical.checksum) != str(artifact.checksum)
    ):
        raise InvalidDocumentGenerationError(
            "Materialized semantic evidence no longer matches its immutable Evidence Artifact."
        )

    payload = decoded.get("payload")
    if not isinstance(payload, dict) or not all(isinstance(key, str) for key in payload):
        raise InvalidDocumentGenerationError(
            "Materialized semantic evidence payload must be an object."
        )
    return payload


def _user_journey_fact(payload: dict[str, object]) -> GenerationUserJourneyFact:
    return GenerationUserJourneyFact(
        journey_name=_string(payload, "journey_name"),
        actors=_string_tuple(payload, "actors"),
        preconditions=_string_tuple(payload, "preconditions"),
        steps=tuple(
            GenerationJourneyStepFact(
                sequence=_integer(item, "sequence"),
                actor=_string(item, "actor"),
                action=_string(item, "action"),
                expected_outcome=_string(item, "expected_outcome"),
                source_reference=_string(item, "source_reference"),
            )
            for item in _object_list(payload, "steps")
        ),
        outcomes=_string_tuple(payload, "outcomes"),
    )


def _deployment_runtime_fact(
    payload: dict[str, object],
) -> GenerationDeploymentRuntimeFact:
    return GenerationDeploymentRuntimeFact(
        environment=_string(payload, "environment"),
        runtime_components=tuple(
            GenerationRuntimeComponentFact(
                name=_string(item, "name"),
                version=_string(item, "version"),
                source_reference=_string(item, "source_reference"),
            )
            for item in _object_list(payload, "runtime_components")
        ),
        prerequisites=_string_tuple(payload, "prerequisites"),
        configuration_keys=_string_tuple(payload, "configuration_keys"),
        deployment_steps=tuple(
            GenerationDeploymentStepFact(
                sequence=_integer(item, "sequence"),
                instruction=_string(item, "instruction"),
                source_reference=_string(item, "source_reference"),
            )
            for item in _object_list(payload, "deployment_steps")
        ),
        verification_checks=tuple(
            GenerationVerificationCheckFact(
                name=_string(item, "name"),
                expected_result=_string(item, "expected_result"),
                source_reference=_string(item, "source_reference"),
            )
            for item in _object_list(payload, "verification_checks")
        ),
        rollback_references=_string_tuple(payload, "rollback_references"),
    )


def _uat_result_fact(payload: dict[str, object]) -> GenerationUatResultFact:
    return GenerationUatResultFact(
        run_reference=_string(payload, "run_reference"),
        executed_at=_string(payload, "executed_at"),
        scenarios=tuple(
            GenerationUatScenarioFact(
                scenario_id=_string(item, "scenario_id"),
                title=_string(item, "title"),
                status=_string(item, "status"),
                expected_result=_string(item, "expected_result"),
                actual_result=_string(item, "actual_result"),
                evidence_references=_string_tuple(item, "evidence_references"),
            )
            for item in _object_list(payload, "scenarios")
        ),
    )


def _object_list(
    payload: dict[str, object],
    key: str,
) -> tuple[dict[str, object], ...]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise InvalidDocumentGenerationError(f"Materialized semantic field {key} must be a list.")
    items: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, dict) or not all(isinstance(name, str) for name in item):
            raise InvalidDocumentGenerationError(
                f"Materialized semantic field {key} must contain objects."
            )
        items.append(item)
    return tuple(items)


def _string_tuple(
    payload: dict[str, object],
    key: str,
) -> tuple[str, ...]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise InvalidDocumentGenerationError(
            f"Materialized semantic field {key} must contain text values."
        )
    return tuple(value)


def _string(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise InvalidDocumentGenerationError(f"Materialized semantic field {key} must be text.")
    return value


def _integer(payload: dict[str, object], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidDocumentGenerationError(
            f"Materialized semantic field {key} must be an integer."
        )
    return value


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
