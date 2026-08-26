# ADR-028: Generate Semantic Documents from Materialized Evidence

- Status: Accepted
- Date: 2026-08-14
- Decision owners: Product Engineering and Technical Documentation

## Context

ADR-026 created typed immutable semantic Evidence Materialization and made readiness depend on it.
ADR-027 removed the mandatory Source identity from Document Version provenance.

The remaining gap is deterministic document generation for semantic evidence-backed document types.

## Decision

1. Add User Guide, Installation Guide, UAT Evidence, and Journey Map to the existing enterprise
   generation profile registry.
2. Reuse `document-readiness-v3` as the only generation eligibility gate.
3. Select only matching materialized semantic Evidence Artifacts.
4. Revalidate the immutable canonical manifest before projecting it into Documents application facts.
5. Keep typed semantic facts in the Documents application port; do not import Evidence types into the
   Documents domain.
6. Use one deterministic renderer with document-type-specific semantic sections.
7. Persist only Evidence Artifact ID/kind/checksum provenance in Document Versions; do not copy
   materialized manifests into Documents persistence.
8. Allow semantic versions to keep `source_id` and `target_run_id` null.
9. Reuse checksum idempotency and the current immutable document lifecycle.
10. Extend the existing Documents UI generation form rather than introduce another generation
    workflow.
11. Never render configuration values or secret-bearing deployment material.
12. Keep SOP, Project Handover, browser collection, live collectors, external resolvers, AI factual
    drafting, and MCP outside this slice.

## Consequences

- four high-value enterprise documents become generatable through one governed pipeline;
- readiness and generation no longer disagree about semantic evidence availability;
- semantic documents remain traceable without fabricated Source/Catalog identifiers;
- User Guide and Journey Map can reuse the same USER_JOURNEY materialization with different
  deterministic render structures;
- existing enterprise profiles remain backward compatible;
- future collectors can target Evidence Materialization without changing document generation policy.
