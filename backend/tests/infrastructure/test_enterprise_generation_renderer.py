from dataclasses import replace

from tdp.modules.documents.application.enterprise_generation_ports import (
    EnterpriseGenerationContext,
    GenerationClaimFact,
    GenerationEvidenceFact,
    GenerationOperationFact,
    GenerationSchemaFact,
)
from tdp.modules.documents.domain.generation import (
    GenerationReadinessFinding,
    GenerationReadinessSnapshot,
    enterprise_generation_profile,
)
from tdp.modules.documents.domain.model import DocumentType
from tdp.modules.documents.infrastructure.enterprise_markdown_renderer import (
    DeterministicEnterpriseMarkdownRenderer,
)


def _context() -> EnterpriseGenerationContext:
    profile = enterprise_generation_profile(DocumentType.LLD)
    assert profile is not None
    return EnterpriseGenerationContext(
        profile=profile,
        readiness=GenerationReadinessSnapshot(
            policy_version="document-readiness-v1",
            state="PARTIALLY_READY",
            eligible=True,
            findings=(
                GenerationReadinessFinding(
                    rule_code="LLD_GOVERNED_CONTEXT_RECOMMENDED",
                    severity="WARNING",
                    message="Implementation context is not yet complete.",
                    missing_input="governed-lld-context",
                    remediation="Add governed LLD context.",
                    supporting_references=(),
                ),
            ),
        ),
        project_id="project-1",
        project_key="DOCS",
        project_name="Documentation Platform",
        project_description="Governed technical documentation.",
        workspace_id="workspace-1",
        source_id="source-1",
        source_name="Commerce API",
        api_title="Commerce API",
        api_version="1.0.0",
        openapi_version="3.1.0",
        target_run_id="run-1",
        source_checksum="a" * 64,
        snapshot_completed_at="2026-08-10T10:00:00+00:00",
        primary_evidence_id="evidence-1",
        primary_evidence_kind="CATALOG_SNAPSHOT",
        available_snapshot_count=1,
        evidence=(
            GenerationEvidenceFact(
                id="evidence-1",
                kind="CATALOG_SNAPSHOT",
                checksum="b" * 64,
                source_reference="synchronization:run-1",
                content_reference="catalog-snapshot:run-1",
                captured_at="2026-08-10T10:00:00+00:00",
            ),
        ),
        claims=(
            GenerationClaimFact(
                id="claim-observed",
                classification="OBSERVED",
                statement="The order endpoint is part of the implementation contract.",
                evidence_ids=("evidence-1",),
                derivation_reference="",
            ),
            GenerationClaimFact(
                id="claim-inferred",
                classification="INFERRED",
                statement="The order capability is grouped under commerce.",
                evidence_ids=("evidence-1",),
                derivation_reference="rule:capability-path-v1",
            ),
            GenerationClaimFact(
                id="claim-unverified",
                classification="UNVERIFIED",
                statement="Production uses blue-green deployment.",
                evidence_ids=(),
                derivation_reference="",
            ),
        ),
        operations=(
            GenerationOperationFact(
                method="GET",
                path="/orders",
                operation_id="listOrders",
                summary="List orders",
                description="Returns the current orders.",
                tags=("orders",),
                deprecated=False,
                security_schemes=("oauth2",),
                parameters=("limit — query; optional; integer",),
                request_body="Not defined",
                responses=("200 — OK; media: application/json; schemas: OrderList",),
                source_pointer="/paths/~1orders/get",
            ),
        ),
        schemas=(
            GenerationSchemaFact(
                name="Order",
                schema_type="object",
                description="Order record.",
                required_fields=("id",),
                properties=("id — string; required",),
                source_pointer="/components/schemas/Order",
            ),
        ),
    )


def test_enterprise_renderer_is_deterministic_and_preserves_claim_strength() -> None:
    renderer = DeterministicEnterpriseMarkdownRenderer()
    context = _context()

    first = renderer.render(context)
    second = renderer.render(context)

    assert first == second
    assert "# Low Level Design: Documentation Platform" in first
    assert "`/paths/~1orders/get`" in first
    assert "**Observed** — The order endpoint is part of the implementation contract." in first
    assert "**Inferred** — The order capability is grouped under commerce." in first
    assert "rule:capability-path-v1" in first
    assert "Production uses blue-green deployment." not in first
    assert "UNVERIFIED LLD-relevant claims excluded from factual sections: **1**." in first
    assert "AI does not determine factual truth" in first


def test_as_built_renderer_keeps_only_observed_statements_factual() -> None:
    profile = enterprise_generation_profile(DocumentType.AS_BUILT)
    assert profile is not None
    base = _context()
    context = replace(
        base,
        profile=profile,
        readiness=GenerationReadinessSnapshot(
            policy_version="document-readiness-v1",
            state="READY",
            eligible=True,
            findings=(),
        ),
        claims=(
            GenerationClaimFact(
                id="claim-asbuilt-observed",
                classification="OBSERVED",
                statement="The orders endpoint is deployed as part of the implemented API surface.",
                evidence_ids=("evidence-1",),
                derivation_reference="",
            ),
            GenerationClaimFact(
                id="claim-asbuilt-inferred",
                classification="INFERRED",
                statement="The service probably uses blue-green deployment.",
                evidence_ids=("evidence-1",),
                derivation_reference="rule:deployment-guess-v1",
            ),
            GenerationClaimFact(
                id="claim-asbuilt-unverified",
                classification="UNVERIFIED",
                statement="The runtime database is PostgreSQL.",
                evidence_ids=(),
                derivation_reference="",
            ),
        ),
    )

    renderer = DeterministicEnterpriseMarkdownRenderer()
    first = renderer.render(context)
    second = renderer.render(context)

    assert first == second
    assert "# As-Built Documentation: Documentation Platform" in first
    assert "The orders endpoint is deployed as part of the implemented API surface." in first
    assert "The service probably uses blue-green deployment." not in first
    assert "The runtime database is PostgreSQL." not in first
    assert "`claim-asbuilt-inferred` — **INFERRED** — excluded" in first
    assert "`claim-asbuilt-unverified` — **UNVERIFIED** — excluded" in first
    assert "INFERRED As-Built claims excluded from factual sections: **1**." in first
    assert "UNVERIFIED As-Built claims excluded from factual sections: **1**." in first
    assert "`/paths/~1orders/get`" in first


def test_hld_renderer_supports_source_only_evidence_without_inventing_catalog_details() -> None:
    profile = enterprise_generation_profile(DocumentType.HLD)
    assert profile is not None
    base = _context()
    context = replace(
        base,
        profile=profile,
        readiness=GenerationReadinessSnapshot(
            policy_version="document-readiness-v1",
            state="PARTIALLY_READY",
            eligible=True,
            findings=(
                GenerationReadinessFinding(
                    rule_code="HLD_GOVERNED_CONTEXT_REQUIRED",
                    severity="WARNING",
                    message="Governed architectural context is not yet complete.",
                    missing_input="governed-hld-context",
                    remediation="Add an observed or deterministically inferred HLD claim.",
                    supporting_references=(),
                ),
            ),
        ),
        target_run_id=None,
        snapshot_completed_at=None,
        primary_evidence_id="source-evidence-1",
        primary_evidence_kind="SOURCE_ARTIFACT",
        available_snapshot_count=0,
        evidence=(
            GenerationEvidenceFact(
                id="source-evidence-1",
                kind="SOURCE_ARTIFACT",
                checksum="c" * 64,
                source_reference="source:source-1",
                content_reference="source-artifact:source-1",
                captured_at="2026-08-10T09:00:00+00:00",
            ),
        ),
        claims=(
            GenerationClaimFact(
                id="claim-hld-unverified",
                classification="UNVERIFIED",
                statement="Production uses an undocumented active-active topology.",
                evidence_ids=(),
                derivation_reference="",
            ),
        ),
        operations=(),
        schemas=(),
    )

    renderer = DeterministicEnterpriseMarkdownRenderer()
    first = renderer.render(context)
    second = renderer.render(context)

    assert first == second
    assert "# High Level Design: Documentation Platform" in first
    assert "Primary evidence kind | `SOURCE_ARTIFACT`" in first
    assert "Not applicable — source evidence" in first
    assert "HLD_GOVERNED_CONTEXT_REQUIRED" in first
    assert "no Catalog snapshot exists" in first
    assert "does not invent a synchronization or implementation detail" in first
    assert "Production uses an undocumented active-active topology." not in first
    assert "UNVERIFIED HLD-relevant claims excluded from factual sections: **1**." in first
    assert "`/paths/~1orders/get`" not in first


def test_hld_renderer_labels_inferred_architectural_context() -> None:
    profile = enterprise_generation_profile(DocumentType.HLD)
    assert profile is not None
    base = _context()
    context = replace(
        base,
        profile=profile,
        readiness=GenerationReadinessSnapshot(
            policy_version="document-readiness-v1",
            state="READY",
            eligible=True,
            findings=(),
        ),
        claims=(
            GenerationClaimFact(
                id="claim-hld-inferred",
                classification="INFERRED",
                statement="The API boundary suggests a commerce-facing service capability.",
                evidence_ids=("evidence-1",),
                derivation_reference="rule:api-boundary-capability-v1",
            ),
        ),
    )

    rendered = DeterministicEnterpriseMarkdownRenderer().render(context)

    expected_inferred = " ".join(
        (
            "**Inferred** — The API boundary suggests a commerce-facing service",
            "capability.",
        )
    )
    assert expected_inferred in rendered
    assert "rule:api-boundary-capability-v1" in rendered
    assert "### Normalized API boundary" in rendered
