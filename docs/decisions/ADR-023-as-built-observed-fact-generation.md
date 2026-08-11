# ADR-023: Extend Generic Enterprise Generation with Strict As-Built Facts

- Status: Accepted
- Date: 2026-08-11
- Decision owners: Product Engineering and Technical Documentation

## Context

ADR-022 established one generic enterprise generation pipeline and proved it with LLD. The next
profile must show that the same pipeline can support a stricter factual contract rather than
drifting toward one application service per document type.

The canonical readiness policy already defines As-Built as requiring both a normalized Catalog
snapshot and a direct `OBSERVED` As-Built claim. It explicitly rejects inference as a substitute
for that observed fact.

## Decision

1. Add `AS_BUILT` to the existing enterprise generation profile registry with profile key
   `enterprise-as-built-v1`.
2. Keep `EnterpriseDocumentGenerationService` unchanged and type-agnostic.
3. Keep the existing cross-context generation input adapter unchanged and profile-neutral.
4. Reuse `CATALOG_SNAPSHOT` as the primary technical evidence kind.
5. Allow only `OBSERVED` As-Built claims in confirmed factual claim sections.
6. Do not render `INFERRED` or `UNVERIFIED` As-Built statements as factual content.
7. Preserve excluded non-observed claim identities and classifications for auditability without
   reproducing their statements as implementation facts.
8. Continue using canonical 0010C readiness as the only eligibility gate.
9. Reuse the existing document series, immutable version, checksum deduplication, workflow,
   approval, and download lifecycle.
10. Introduce no persistence migration and no As-Built-specific application service.
11. Keep Technical Source Overview and LLD behavior unchanged.
12. Keep AI outside factual truth, readiness, and evidence classification.

## Renderer decision

The deterministic enterprise Markdown renderer performs a minimal dispatch using the canonical
generation-profile document type. Common operation, schema, evidence, and formatting helpers remain
shared while As-Built receives its own composition method.

A separate application service or persistence path is not justified because the differences are
document composition and factual claim policy, not lifecycle orchestration.

## Consequences

- The generic generation architecture is proven across two profiles with different claim-strength
  rules.
- As-Built cannot be generated from inferred implementation assumptions alone.
- The document remains useful with the evidence currently supported by the platform while
  explicitly exposing its evidence boundary.
- Future profiles can reuse the same application pipeline and add composition behavior only where
  their document contract differs.
