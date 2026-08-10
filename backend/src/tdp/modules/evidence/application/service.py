import hashlib
import json
from dataclasses import asdict

from tdp.modules.catalog.domain.model import (
    ApiOperation,
    ApiSchema,
    SynchronizationId,
    SynchronizationStatus,
)
from tdp.modules.catalog.domain.repository import CatalogRepository
from tdp.modules.documents.domain.governance import DOCUMENT_TYPE_REGISTRY
from tdp.modules.evidence.application.commands import (
    CreateClaimCommand,
    RegisterSnapshotEvidenceCommand,
    RegisterSourceEvidenceCommand,
)
from tdp.modules.evidence.application.dto import ClaimDto, EvidenceArtifactDto
from tdp.modules.evidence.domain.errors import (
    ClaimNotFoundError,
    EvidenceArtifactNotFoundError,
    EvidenceFeatureArchivedError,
    EvidenceFeatureNotFoundError,
    EvidenceProjectArchivedError,
    EvidenceProjectNotFoundError,
    EvidenceSnapshotNotCompletedError,
    EvidenceSnapshotNotFoundError,
    EvidenceSourceNotFoundError,
    EvidenceWorkspaceArchivedError,
    EvidenceWorkspaceNotFoundError,
    InvalidClaimClassificationError,
    InvalidClaimDocumentTypeError,
    InvalidClaimEvidenceError,
)
from tdp.modules.evidence.domain.model import (
    Claim,
    ClaimClassification,
    ClaimId,
    EvidenceArtifact,
    EvidenceArtifactId,
    EvidenceCollectionMethod,
    EvidenceKind,
    EvidenceSourceSystem,
)
from tdp.modules.evidence.domain.repository import EvidenceRepository
from tdp.modules.features.domain.model import FeatureId, FeatureStatus
from tdp.modules.features.domain.repository import FeatureRepository
from tdp.modules.projects.domain.model import Project, ProjectId, ProjectStatus
from tdp.modules.projects.domain.repository import ProjectRepository
from tdp.modules.sources.domain.model import SourceId
from tdp.modules.sources.domain.repository import SourceRepository
from tdp.modules.workspaces.domain.model import WorkspaceId, WorkspaceStatus
from tdp.modules.workspaces.domain.repository import WorkspaceRepository


class EvidenceApplicationService:
    def __init__(
        self,
        repository: EvidenceRepository,
        project_repository: ProjectRepository,
        workspace_repository: WorkspaceRepository,
        feature_repository: FeatureRepository,
        source_repository: SourceRepository,
        catalog_repository: CatalogRepository,
    ) -> None:
        self._repository = repository
        self._project_repository = project_repository
        self._workspace_repository = workspace_repository
        self._feature_repository = feature_repository
        self._source_repository = source_repository
        self._catalog_repository = catalog_repository

    async def register_source_artifact(
        self,
        command: RegisterSourceEvidenceCommand,
    ) -> EvidenceArtifactDto:
        project = await self._require_project(command.project_id, writable=True)
        source = await self._source_repository.get(SourceId.from_string(command.source_id))
        if source is None or str(source.project_id) != command.project_id:
            raise EvidenceSourceNotFoundError(
                f"Source {command.source_id} was not found for project {command.project_id}."
            )

        existing = await self._repository.get_artifact_by_origin(
            EvidenceKind.SOURCE_ARTIFACT,
            str(source.id),
        )
        if existing is not None:
            return EvidenceArtifactDto.from_domain(existing)

        artifact = EvidenceArtifact.create(
            workspace_id=project.workspace_id,
            project_id=str(project.id),
            kind=EvidenceKind.SOURCE_ARTIFACT,
            source_system=EvidenceSourceSystem.SOURCE_REGISTRY,
            source_reference=f"source:{source.id}",
            origin_id=str(source.id),
            checksum=str(source.checksum),
            content_reference=f"source-artifact:{source.id}",
            collection_method=EvidenceCollectionMethod.SOURCE_IMPORT,
            collected_by=command.principal.audit_actor,
            captured_at=source.created_at,
        )
        await self._repository.add_artifact(artifact)
        return EvidenceArtifactDto.from_domain(artifact)

    async def register_catalog_snapshot(
        self,
        command: RegisterSnapshotEvidenceCommand,
    ) -> EvidenceArtifactDto:
        project = await self._require_project(command.project_id, writable=True)
        run_id = SynchronizationId.from_string(command.synchronization_id)
        run = await self._catalog_repository.get_run(run_id)
        if run is None or run.project_id != command.project_id:
            raise EvidenceSnapshotNotFoundError(
                f"Synchronization {command.synchronization_id} was not found "
                f"for project {command.project_id}."
            )
        if run.status is not SynchronizationStatus.COMPLETED or run.completed_at is None:
            raise EvidenceSnapshotNotCompletedError(
                "Only completed synchronization snapshots can become evidence artifacts."
            )

        existing = await self._repository.get_artifact_by_origin(
            EvidenceKind.CATALOG_SNAPSHOT,
            str(run.id),
        )
        if existing is not None:
            return EvidenceArtifactDto.from_domain(existing)

        operations = await self._catalog_repository.list_operations_by_run(run.id)
        schemas = await self._catalog_repository.list_schemas_by_run(run.id)
        checksum = _snapshot_checksum(run.source_checksum, operations, schemas)

        artifact = EvidenceArtifact.create(
            workspace_id=project.workspace_id,
            project_id=str(project.id),
            kind=EvidenceKind.CATALOG_SNAPSHOT,
            source_system=EvidenceSourceSystem.API_CATALOG,
            source_reference=f"synchronization:{run.id}",
            origin_id=str(run.id),
            checksum=checksum,
            content_reference=f"catalog-snapshot:{run.id}",
            collection_method=EvidenceCollectionMethod.DETERMINISTIC_NORMALIZATION,
            collected_by=command.principal.audit_actor,
            captured_at=run.completed_at,
        )
        await self._repository.add_artifact(artifact)
        return EvidenceArtifactDto.from_domain(artifact)

    async def list_evidence(self, project_id: str) -> list[EvidenceArtifactDto]:
        await self._require_project(project_id, writable=False)
        artifacts = await self._repository.list_artifacts_by_project(project_id)
        return [EvidenceArtifactDto.from_domain(item) for item in artifacts]

    async def get_evidence(self, artifact_id: str) -> EvidenceArtifactDto:
        artifact = await self._repository.get_artifact(EvidenceArtifactId.from_string(artifact_id))
        if artifact is None:
            raise EvidenceArtifactNotFoundError(f"Evidence artifact {artifact_id} was not found.")
        return EvidenceArtifactDto.from_domain(artifact)

    async def create_claim(self, command: CreateClaimCommand) -> ClaimDto:
        project = await self._require_project(command.project_id, writable=True)
        feature_id = await self._validate_feature(
            command.project_id,
            command.feature_id,
            writable=True,
        )
        classification = _claim_classification(command.classification)
        evidence_ids = tuple(EvidenceArtifactId.from_string(item) for item in command.evidence_ids)
        await self._validate_claim_evidence(command.project_id, feature_id, evidence_ids)
        document_types = _normalize_document_types(command.relevant_document_types)

        claim = Claim.create(
            workspace_id=project.workspace_id,
            project_id=str(project.id),
            feature_id=feature_id,
            statement=command.statement,
            classification=classification,
            evidence_ids=evidence_ids,
            derivation_reference=command.derivation_reference,
            relevant_document_types=document_types,
            asserted_by=command.principal.audit_actor,
        )
        await self._repository.add_claim(claim)
        return ClaimDto.from_domain(claim)

    async def list_claims(self, project_id: str) -> list[ClaimDto]:
        await self._require_project(project_id, writable=False)
        claims = await self._repository.list_claims_by_project(project_id)
        return [ClaimDto.from_domain(item) for item in claims]

    async def get_claim(self, claim_id: str) -> ClaimDto:
        claim = await self._repository.get_claim(ClaimId.from_string(claim_id))
        if claim is None:
            raise ClaimNotFoundError(f"Claim {claim_id} was not found.")
        return ClaimDto.from_domain(claim)

    async def _require_project(self, project_id: str, *, writable: bool) -> Project:
        project = await self._project_repository.get(ProjectId.from_string(project_id))
        if project is None:
            raise EvidenceProjectNotFoundError(f"Project {project_id} was not found.")

        workspace = await self._workspace_repository.get(
            WorkspaceId.from_string(project.workspace_id)
        )
        if workspace is None:
            raise EvidenceWorkspaceNotFoundError(
                f"Workspace {project.workspace_id} for project {project_id} was not found."
            )

        if writable and project.status is ProjectStatus.ARCHIVED:
            raise EvidenceProjectArchivedError(
                "Evidence and claim mutations are not allowed for an archived project."
            )
        if writable and workspace.status is WorkspaceStatus.ARCHIVED:
            raise EvidenceWorkspaceArchivedError(
                "Evidence and claim mutations are not allowed for an archived workspace."
            )
        return project

    async def _validate_feature(
        self,
        project_id: str,
        feature_id: str | None,
        *,
        writable: bool,
    ) -> str | None:
        if feature_id is None:
            return None

        feature = await self._feature_repository.get(FeatureId.from_string(feature_id))
        if feature is None or feature.project_id != project_id:
            raise EvidenceFeatureNotFoundError(
                f"Feature {feature_id} was not found for project {project_id}."
            )
        if writable and feature.status is FeatureStatus.ARCHIVED:
            raise EvidenceFeatureArchivedError(
                "New claims cannot be scoped to an archived feature."
            )
        return str(feature.id)

    async def _validate_claim_evidence(
        self,
        project_id: str,
        feature_id: str | None,
        evidence_ids: tuple[EvidenceArtifactId, ...],
    ) -> None:
        for evidence_id in evidence_ids:
            artifact = await self._repository.get_artifact(evidence_id)
            if artifact is None:
                raise InvalidClaimEvidenceError(f"Evidence artifact {evidence_id} does not exist.")
            if artifact.project_id != project_id:
                raise InvalidClaimEvidenceError(
                    "A claim cannot reference evidence from another project."
                )
            if (
                feature_id is not None
                and artifact.feature_id is not None
                and artifact.feature_id != feature_id
            ):
                raise InvalidClaimEvidenceError(
                    "A feature-scoped claim cannot reference evidence scoped to another feature."
                )


def _claim_classification(value: str) -> ClaimClassification:
    try:
        return ClaimClassification(value.strip().upper())
    except ValueError as exc:
        raise InvalidClaimClassificationError(
            "Claim classification must be OBSERVED, INFERRED, or UNVERIFIED."
        ) from exc


def _normalize_document_types(values: tuple[str, ...]) -> tuple[str, ...]:
    requested = {value.strip().upper() for value in values if value.strip()}
    allowed_order = [item.document_type.value for item in DOCUMENT_TYPE_REGISTRY]
    invalid = sorted(requested.difference(allowed_order))
    if invalid:
        raise InvalidClaimDocumentTypeError(
            "Unknown governed document type(s): " + ", ".join(invalid)
        )
    return tuple(item for item in allowed_order if item in requested)


def _snapshot_checksum(
    source_checksum: str,
    operations: list[ApiOperation],
    schemas: list[ApiSchema],
) -> str:
    normalized_operations = []
    for operation in sorted(operations, key=lambda item: (item.method, item.path)):
        record = asdict(operation)
        record.pop("synchronization_id", None)
        record.pop("project_id", None)
        record.pop("source_id", None)
        normalized_operations.append(record)

    normalized_schemas = []
    for schema in sorted(schemas, key=lambda item: item.name):
        record = asdict(schema)
        record.pop("synchronization_id", None)
        record.pop("project_id", None)
        record.pop("source_id", None)
        normalized_schemas.append(record)

    payload = {
        "source_checksum": source_checksum,
        "operations": normalized_operations,
        "schemas": normalized_schemas,
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
