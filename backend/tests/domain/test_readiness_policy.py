from tdp.modules.readiness.domain.model import (
    DeterministicReadinessEvaluator,
    ReadinessClaimFact,
    ReadinessDocumentFact,
    ReadinessEvidenceFact,
    ReadinessFindingSeverity,
    ReadinessState,
)
from tdp.modules.readiness.domain.policy import (
    READINESS_POLICY_VERSION,
    READINESS_PROFILES,
    readiness_profile,
)


def test_readiness_profiles_cover_the_ten_enterprise_document_types_in_order() -> None:
    assert READINESS_POLICY_VERSION == "document-readiness-v1"
    assert [item.document_type for item in READINESS_PROFILES] == [
        "HLD",
        "LLD",
        "AS_BUILT",
        "SOP",
        "USER_GUIDE",
        "INSTALLATION_GUIDE",
        "PROJECT_HANDOVER",
        "UAT_EVIDENCE",
        "JOURNEY_MAP",
        "DEVELOPER_ONBOARDING_BRIEF",
    ]


def test_hld_progresses_from_not_ready_to_partial_to_ready_deterministically() -> None:
    evaluator = DeterministicReadinessEvaluator()
    profile = readiness_profile("HLD")

    empty = evaluator.evaluate(
        profile=profile,
        evidence=(),
        claims=(),
        documents=(),
    )
    assert empty.state is ReadinessState.NOT_READY
    assert empty.eligible is False
    assert any(item.rule_code == "HLD_TECHNICAL_EVIDENCE_REQUIRED" for item in empty.findings)

    evidence = (ReadinessEvidenceFact(reference="evidence:1", kind="SOURCE_ARTIFACT"),)
    partial = evaluator.evaluate(
        profile=profile,
        evidence=evidence,
        claims=(),
        documents=(),
    )
    assert partial.state is ReadinessState.PARTIALLY_READY
    assert partial.eligible is True
    assert [item.severity for item in partial.findings] == [ReadinessFindingSeverity.WARNING]

    claims = (
        ReadinessClaimFact(
            reference="claim:1",
            classification="OBSERVED",
            relevant_document_types=("HLD",),
        ),
    )
    ready = evaluator.evaluate(
        profile=profile,
        evidence=evidence,
        claims=claims,
        documents=(),
    )
    assert ready.state is ReadinessState.READY
    assert ready.eligible is True
    assert ready.findings == ()


def test_as_built_rejects_inference_as_a_substitute_for_observed_fact() -> None:
    evaluator = DeterministicReadinessEvaluator()
    result = evaluator.evaluate(
        profile=readiness_profile("AS_BUILT"),
        evidence=(ReadinessEvidenceFact(reference="evidence:1", kind="CATALOG_SNAPSHOT"),),
        claims=(
            ReadinessClaimFact(
                reference="claim:1",
                classification="INFERRED",
                relevant_document_types=("AS_BUILT",),
            ),
        ),
        documents=(),
    )

    assert result.state is ReadinessState.NOT_READY
    finding = next(
        item for item in result.findings if item.rule_code == "ASBUILT_OBSERVED_CLAIM_REQUIRED"
    )
    assert finding.severity is ReadinessFindingSeverity.BLOCKER
    assert finding.supporting_references == ("claim:1:INFERRED",)


def test_handover_requires_approved_versions_of_the_required_bundle() -> None:
    evaluator = DeterministicReadinessEvaluator()
    required = (
        "HLD",
        "LLD",
        "AS_BUILT",
        "SOP",
        "USER_GUIDE",
        "INSTALLATION_GUIDE",
    )
    incomplete = tuple(
        ReadinessDocumentFact(
            reference=f"document:{document_type}",
            document_type=document_type,
            status="APPROVED" if document_type != "SOP" else "IN_REVIEW",
        )
        for document_type in required
    )

    blocked = evaluator.evaluate(
        profile=readiness_profile("PROJECT_HANDOVER"),
        evidence=(),
        claims=(),
        documents=incomplete,
    )
    assert blocked.state is ReadinessState.NOT_READY
    assert blocked.eligible is False
    assert blocked.findings[0].missing_input == "approved-documents:SOP"

    approved = tuple(
        ReadinessDocumentFact(
            reference=f"document:{document_type}",
            document_type=document_type,
            status="APPROVED",
        )
        for document_type in required
    )
    ready = evaluator.evaluate(
        profile=readiness_profile("PROJECT_HANDOVER"),
        evidence=(),
        claims=(),
        documents=approved,
    )
    assert ready.state is ReadinessState.READY
    assert ready.eligible is True
