from dataclasses import dataclass

from tdp.modules.evidence.domain.materialization import EvidenceMaterialization
from tdp.modules.evidence.domain.model import Claim, EvidenceArtifact


@dataclass(frozen=True, slots=True)
class EvidenceArtifactDto:
    id: str
    workspace_id: str
    project_id: str
    feature_id: str | None
    kind: str
    source_system: str
    source_reference: str
    origin_id: str
    checksum: str
    content_reference: str
    collection_method: str
    collected_by: str
    captured_at: str
    created_at: str

    @classmethod
    def from_domain(cls, artifact: EvidenceArtifact) -> "EvidenceArtifactDto":
        return cls(
            id=str(artifact.id),
            workspace_id=artifact.workspace_id,
            project_id=artifact.project_id,
            feature_id=artifact.feature_id,
            kind=artifact.kind.value,
            source_system=artifact.source_system.value,
            source_reference=artifact.source_reference,
            origin_id=artifact.origin_id,
            checksum=str(artifact.checksum),
            content_reference=artifact.content_reference,
            collection_method=artifact.collection_method.value,
            collected_by=artifact.collected_by,
            captured_at=artifact.captured_at.isoformat(),
            created_at=artifact.created_at.isoformat(),
        )


@dataclass(frozen=True, slots=True)
class EvidenceMaterializationDto:
    evidence_id: str
    project_id: str
    kind: str
    schema_version: str
    checksum: str
    materialized_by: str
    materialized_at: str

    @classmethod
    def from_domain(
        cls,
        materialization: EvidenceMaterialization,
    ) -> "EvidenceMaterializationDto":
        return cls(
            evidence_id=str(materialization.evidence_id),
            project_id=materialization.project_id,
            kind=materialization.kind.value,
            schema_version=materialization.schema_version,
            checksum=str(materialization.checksum),
            materialized_by=materialization.materialized_by,
            materialized_at=materialization.materialized_at.isoformat(),
        )


@dataclass(frozen=True, slots=True)
class ClaimDto:
    id: str
    workspace_id: str
    project_id: str
    feature_id: str | None
    statement: str
    classification: str
    evidence_ids: list[str]
    derivation_reference: str
    relevant_document_types: list[str]
    asserted_by: str
    created_at: str

    @classmethod
    def from_domain(cls, claim: Claim) -> "ClaimDto":
        return cls(
            id=str(claim.id),
            workspace_id=claim.workspace_id,
            project_id=claim.project_id,
            feature_id=claim.feature_id,
            statement=claim.statement,
            classification=claim.classification.value,
            evidence_ids=[str(item) for item in claim.evidence_ids],
            derivation_reference=claim.derivation_reference,
            relevant_document_types=list(claim.relevant_document_types),
            asserted_by=claim.asserted_by,
            created_at=claim.created_at.isoformat(),
        )
