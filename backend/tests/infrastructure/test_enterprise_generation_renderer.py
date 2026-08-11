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
