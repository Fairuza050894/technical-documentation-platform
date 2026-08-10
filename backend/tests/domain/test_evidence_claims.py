from datetime import UTC, datetime

import pytest

from tdp.modules.evidence.domain.errors import (
    InvalidClaimDerivationError,
    InvalidClaimEvidenceError,
)
from tdp.modules.evidence.domain.model import (
    Claim,
    ClaimClassification,
    EvidenceArtifact,
    EvidenceArtifactId,
    EvidenceCollectionMethod,
    EvidenceKind,
    EvidenceSourceSystem,
)


def _artifact() -> EvidenceArtifact:
    return EvidenceArtifact.create(
        workspace_id="workspace-1",
        project_id="project-1",
        kind=EvidenceKind.SOURCE_ARTIFACT,
        source_system=EvidenceSourceSystem.SOURCE_REGISTRY,
        source_reference="source:source-1",
        origin_id="source-1",
        checksum="a" * 64,
        content_reference="source-artifact:source-1",
        collection_method=EvidenceCollectionMethod.SOURCE_IMPORT,
        collected_by="Technical Writer",
        captured_at=datetime(2026, 8, 10, 1, 0, tzinfo=UTC),
    )


def test_evidence_artifact_is_immutable_and_checksum_backed() -> None:
    artifact = _artifact()

    assert str(artifact.checksum) == "a" * 64
    assert artifact.kind is EvidenceKind.SOURCE_ARTIFACT
    with pytest.raises(AttributeError):
        artifact.project_id = "other-project"  # type: ignore[misc]


def test_observed_claim_requires_supporting_evidence() -> None:
    with pytest.raises(InvalidClaimEvidenceError):
        Claim.create(
            workspace_id="workspace-1",
            project_id="project-1",
            statement="The API exposes an order endpoint.",
            classification=ClaimClassification.OBSERVED,
            evidence_ids=(),
            derivation_reference="",
            relevant_document_types=("LLD",),
            asserted_by="Technical Writer",
        )


def test_inferred_claim_requires_evidence_and_derivation_trace() -> None:
    evidence_id = EvidenceArtifactId.new()

    with pytest.raises(InvalidClaimDerivationError):
        Claim.create(
            workspace_id="workspace-1",
            project_id="project-1",
            statement="The order capability depends on the payment capability.",
            classification=ClaimClassification.INFERRED,
            evidence_ids=(evidence_id,),
            derivation_reference="",
            relevant_document_types=("HLD",),
            asserted_by="Technical Writer",
        )

    claim = Claim.create(
        workspace_id="workspace-1",
        project_id="project-1",
        statement="The order capability depends on the payment capability.",
        classification=ClaimClassification.INFERRED,
        evidence_ids=(evidence_id,),
        derivation_reference="rule:api-path-dependency-v1",
        relevant_document_types=("HLD",),
        asserted_by="Technical Writer",
    )

    assert claim.classification is ClaimClassification.INFERRED
    assert claim.derivation_reference == "rule:api-path-dependency-v1"


def test_unverified_claim_cannot_carry_a_derivation_rule() -> None:
    with pytest.raises(InvalidClaimDerivationError):
        Claim.create(
            workspace_id="workspace-1",
            project_id="project-1",
            statement="Operations prefer blue-green deployment.",
            classification=ClaimClassification.UNVERIFIED,
            evidence_ids=(),
            derivation_reference="rule:unsupported",
            relevant_document_types=("HLD",),
            asserted_by="Technical Writer",
        )
