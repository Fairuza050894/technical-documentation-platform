from datetime import datetime

from tdp.modules.documents.domain.governance import (
    DOCUMENT_TYPE_REGISTRY,
    PROJECT_DOCUMENTATION_POLICY,
    ProjectDocumentAvailability,
    document_type_definition,
)
from tdp.modules.documents.domain.model import DocumentType, DocumentVersion
from tdp.modules.documents.domain.repository import DocumentRepository
from tdp.modules.evidence.domain.model import Claim, EvidenceArtifact
from tdp.modules.evidence.domain.repository import EvidenceRepository
from tdp.modules.projects.domain.model import ProjectId
from tdp.modules.projects.domain.repository import ProjectRepository
from tdp.modules.readiness.application.dto import (
    DocumentReadinessDto,
    ProjectReadinessDto,
)
from tdp.modules.readiness.domain.errors import (
    InvalidReadinessDocumentTypeError,
    ReadinessProjectNotFoundError,
)
from tdp.modules.readiness.domain.model import (
    DeterministicReadinessEvaluator,
    ReadinessClaimFact,
    ReadinessDocumentFact,
    ReadinessEvidenceFact,
)
from tdp.modules.readiness.domain.policy import (
    READINESS_PROFILES,
    readiness_profile,
)


class ReadinessApplicationService:
    def __init__(
        self,
        project_repository: ProjectRepository,
        evidence_repository: EvidenceRepository,
        document_repository: DocumentRepository,
        evaluator: DeterministicReadinessEvaluator | None = None,
    ) -> None:
        self._project_repository = project_repository
        self._evidence_repository = evidence_repository
        self._document_repository = document_repository
        self._evaluator = evaluator or DeterministicReadinessEvaluator()

    async def project_readiness(self, project_id: str) -> ProjectReadinessDto:
        project = await self._project_repository.get(ProjectId.from_string(project_id))
        if project is None:
            raise ReadinessProjectNotFoundError(f"Project {project_id} was not found.")

        evidence = await self._evidence_repository.list_artifacts_by_project(project_id)
        materializations = await self._evidence_repository.list_materializations_by_project(
            project_id
        )
        claims = await self._evidence_repository.list_claims_by_project(project_id)
        versions = await self._document_repository.list_versions_by_project(project_id)

        materialized_ids = {str(item.evidence_id) for item in materializations}
        evidence_facts = _evidence_facts(evidence, materialized_ids)
        claim_facts = _claim_facts(claims)
        latest_versions = _latest_governed_versions(versions)
        document_facts = _document_facts(latest_versions)
        requirements = {
            item.document_type.value: item.requirement.value
            for item in PROJECT_DOCUMENTATION_POLICY
        }

        items: list[DocumentReadinessDto] = []
        for registry_item in DOCUMENT_TYPE_REGISTRY:
            document_type = registry_item.document_type
            assessment = self._evaluator.evaluate(
                profile=readiness_profile(document_type.value),
                evidence=evidence_facts,
                claims=claim_facts,
                documents=document_facts,
            )
            latest = latest_versions.get(document_type)
            definition = document_type_definition(document_type)
            items.append(
                DocumentReadinessDto.from_assessment(
                    project_id=str(project.id),
                    display_name=definition.display_name,
                    automation_profile=definition.automation_profile.value,
                    requirement=requirements[document_type.value],
                    availability=(
                        ProjectDocumentAvailability.AVAILABLE.value
                        if latest is not None
                        else ProjectDocumentAvailability.MISSING.value
                    ),
                    latest_status=latest.status.value if latest is not None else None,
                    assessment=assessment,
                )
            )

        return ProjectReadinessDto.create(
            project_id=str(project.id),
            project_status=project.status.value,
            items=items,
        )

    async def document_readiness(
        self,
        project_id: str,
        document_type: str,
    ) -> DocumentReadinessDto:
        normalized = document_type.strip().upper()
        if normalized not in {profile.document_type for profile in READINESS_PROFILES}:
            raise InvalidReadinessDocumentTypeError(
                f"{document_type} is not a governed Project document type."
            )

        project = await self.project_readiness(project_id)
        return next(item for item in project.items if item.document_type == normalized)


def _evidence_facts(
    evidence: list[EvidenceArtifact],
    materialized_ids: set[str],
) -> tuple[ReadinessEvidenceFact, ...]:
    return tuple(
        ReadinessEvidenceFact(
            reference=f"evidence:{item.id}",
            kind=item.kind.value,
            materialized=str(item.id) in materialized_ids,
        )
        for item in evidence
    )


def _claim_facts(
    claims: list[Claim],
) -> tuple[ReadinessClaimFact, ...]:
    return tuple(
        ReadinessClaimFact(
            reference=f"claim:{item.id}",
            classification=item.classification.value,
            relevant_document_types=item.relevant_document_types,
        )
        for item in claims
    )


def _latest_governed_versions(
    versions: list[DocumentVersion],
) -> dict[DocumentType, DocumentVersion]:
    governed_types = {item.document_type for item in DOCUMENT_TYPE_REGISTRY}
    latest_by_type: dict[DocumentType, DocumentVersion] = {}
    for version in versions:
        if version.document_type not in governed_types:
            continue
        current = latest_by_type.get(version.document_type)
        if current is None or _version_sort_key(version) > _version_sort_key(current):
            latest_by_type[version.document_type] = version
    return latest_by_type


def _document_facts(
    latest_versions: dict[DocumentType, DocumentVersion],
) -> tuple[ReadinessDocumentFact, ...]:
    return tuple(
        ReadinessDocumentFact(
            reference=f"document:{version.document_id}:version:{version.id}",
            document_type=document_type.value,
            status=version.status.value,
        )
        for document_type, version in latest_versions.items()
    )


def _version_sort_key(version: DocumentVersion) -> tuple[datetime, int, int, str]:
    return (
        version.created_at,
        version.version_number.major,
        version.version_number.minor,
        str(version.id),
    )
