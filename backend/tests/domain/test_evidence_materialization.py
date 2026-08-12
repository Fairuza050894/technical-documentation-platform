from datetime import UTC, datetime

import pytest

from tdp.modules.evidence.domain.errors import (
    EvidenceMaterializationChecksumMismatchError,
    InvalidEvidenceManifestError,
)
from tdp.modules.evidence.domain.materialization import (
    SEMANTIC_EVIDENCE_MANIFEST_SCHEMA_VERSION,
    EvidenceMaterialization,
    canonicalize_semantic_evidence_manifest,
)
from tdp.modules.evidence.domain.model import (
    EvidenceArtifactId,
    EvidenceChecksum,
    EvidenceKind,
)


def deployment_manifest() -> dict[str, object]:
    return {
        "schema_version": SEMANTIC_EVIDENCE_MANIFEST_SCHEMA_VERSION,
        "kind": "DEPLOYMENT_RUNTIME",
        "payload": {
            "environment": "staging",
            "runtime_components": [
                {
                    "name": "api",
                    "version": "1.4.0",
                    "source_reference": "deployment-run:release-42",
                }
            ],
            "prerequisites": ["Container runtime is available."],
            "configuration_keys": ["DATABASE_URL", "spring.profiles.active"],
            "deployment_steps": [
                {
                    "sequence": 1,
                    "instruction": "Apply the approved deployment bundle.",
                    "source_reference": "pipeline-step:deploy",
                }
            ],
            "verification_checks": [
                {
                    "name": "Readiness endpoint",
                    "expected_result": "The readiness check reports healthy.",
                    "source_reference": "pipeline-step:verify",
                }
            ],
            "rollback_references": ["runbook:rollback-release-42"],
        },
    }


def user_journey_manifest() -> dict[str, object]:
    return {
        "schema_version": SEMANTIC_EVIDENCE_MANIFEST_SCHEMA_VERSION,
        "kind": "USER_JOURNEY",
        "payload": {
            "journey_name": "Checkout",
            "actors": ["Operator"],
            "preconditions": ["The operator is signed in."],
            "steps": [
                {
                    "sequence": 1,
                    "actor": "Operator",
                    "action": "Submit the checkout form.",
                    "expected_outcome": "The order is accepted.",
                    "source_reference": "journey-step:checkout-submit",
                }
            ],
            "outcomes": ["The order is visible in monitoring."],
        },
    }


def uat_result_manifest() -> dict[str, object]:
    return {
        "schema_version": SEMANTIC_EVIDENCE_MANIFEST_SCHEMA_VERSION,
        "kind": "UAT_RESULT",
        "payload": {
            "run_reference": "uat-run:release-42",
            "executed_at": "2026-08-12T04:00:00+00:00",
            "scenarios": [
                {
                    "scenario_id": "UAT-001",
                    "title": "Checkout succeeds",
                    "status": "PASSED",
                    "expected_result": "The order is created.",
                    "actual_result": "The order was created.",
                    "evidence_references": ["uat-evidence:checkout-001"],
                }
            ],
        },
    }


@pytest.mark.parametrize(
    ("kind", "manifest"),
    [
        (EvidenceKind.USER_JOURNEY, user_journey_manifest()),
        (EvidenceKind.DEPLOYMENT_RUNTIME, deployment_manifest()),
        (EvidenceKind.UAT_RESULT, uat_result_manifest()),
    ],
)
def test_semantic_manifests_are_typed_canonical_and_deterministic(
    kind: EvidenceKind,
    manifest: dict[str, object],
) -> None:
    first = canonicalize_semantic_evidence_manifest(kind, manifest)
    second = canonicalize_semantic_evidence_manifest(kind, manifest)

    assert first == second
    assert first.schema_version == SEMANTIC_EVIDENCE_MANIFEST_SCHEMA_VERSION
    assert first.kind is kind
    assert str(first.checksum) == str(second.checksum)
    assert first.canonical_json.startswith('{"kind":')


def test_materialization_requires_checksum_alignment_with_evidence_artifact() -> None:
    canonical = canonicalize_semantic_evidence_manifest(
        EvidenceKind.DEPLOYMENT_RUNTIME,
        deployment_manifest(),
    )

    materialization = EvidenceMaterialization.create(
        evidence_id=EvidenceArtifactId.new(),
        project_id="project-1",
        expected_checksum=canonical.checksum,
        manifest=canonical,
        materialized_by="Release Engineer",
        materialized_at=datetime(2026, 8, 12, 4, 0, tzinfo=UTC),
    )
    assert materialization.checksum == canonical.checksum

    with pytest.raises(EvidenceMaterializationChecksumMismatchError):
        EvidenceMaterialization.create(
            evidence_id=EvidenceArtifactId.new(),
            project_id="project-1",
            expected_checksum=EvidenceChecksum("f" * 64),
            manifest=canonical,
            materialized_by="Release Engineer",
            materialized_at=datetime(2026, 8, 12, 4, 0, tzinfo=UTC),
        )


def test_semantic_manifest_rejects_secret_values_and_direct_urls() -> None:
    secret = deployment_manifest()
    secret_payload = secret["payload"]
    assert isinstance(secret_payload, dict)
    secret_payload["deployment_steps"] = [
        {
            "sequence": 1,
            "instruction": "Use password=super-secret before deployment.",
            "source_reference": "pipeline-step:deploy",
        }
    ]
    with pytest.raises(InvalidEvidenceManifestError):
        canonicalize_semantic_evidence_manifest(
            EvidenceKind.DEPLOYMENT_RUNTIME,
            secret,
        )

    direct_url = deployment_manifest()
    direct_payload = direct_url["payload"]
    assert isinstance(direct_payload, dict)
    direct_payload["rollback_references"] = ["https://internal.invalid/rollback"]
    with pytest.raises(InvalidEvidenceManifestError):
        canonicalize_semantic_evidence_manifest(
            EvidenceKind.DEPLOYMENT_RUNTIME,
            direct_url,
        )


def test_deployment_manifest_accepts_configuration_names_but_not_values() -> None:
    valid = deployment_manifest()
    canonical = canonicalize_semantic_evidence_manifest(
        EvidenceKind.DEPLOYMENT_RUNTIME,
        valid,
    )
    assert "DATABASE_URL" in canonical.canonical_json

    invalid = deployment_manifest()
    invalid_payload = invalid["payload"]
    assert isinstance(invalid_payload, dict)
    invalid_payload["configuration_keys"] = ["DATABASE_URL=postgres://secret"]
    with pytest.raises(InvalidEvidenceManifestError):
        canonicalize_semantic_evidence_manifest(
            EvidenceKind.DEPLOYMENT_RUNTIME,
            invalid,
        )
