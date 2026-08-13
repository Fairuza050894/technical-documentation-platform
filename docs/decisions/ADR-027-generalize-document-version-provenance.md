# ADR-027: Generalize Document Version Provenance

- Status: Accepted
- Date: 2026-08-13
- Decision owners: Product Engineering and Technical Documentation

## Context

The enterprise generator currently persists `source_id` on every Document Version. This was correct
for Technical Source Overview, LLD, As-Built, and the current HLD profiles, but it is not a universal
truth.

ADR-026 introduced checksum-verified semantic Evidence Materialization. A future Installation Guide
can legitimately originate from `DEPLOYMENT_RUNTIME` evidence without any Source Registry record or
Catalog synchronization.

Making a semantic generator fabricate a Source ID would corrupt provenance.

## Decision

1. Make `DocumentVersion.source_id` nullable.
2. Keep `target_run_id` nullable and retain both compatibility fields for existing consumers.
3. Add `DocumentProvenanceReference` to the Documents domain.
4. Support provenance kinds `SOURCE_REGISTRY`, `CATALOG_SYNCHRONIZATION`, and
   `EVIDENCE_ARTIFACT`.
5. Persist provenance in a separate append-only `document_version_provenance` relation rather than
   adding one `primary_evidence_id` column.
6. Store Evidence Artifact references, Evidence kind, and checksum only; do not copy Evidence
   payloads or canonical materialized manifests.
7. Backfill historical Source/Catalog provenance deterministically from existing columns.
8. Do not infer missing historical Evidence Artifact IDs.
9. Have the generic enterprise generation service persist every governed Evidence Artifact selected
   by its input provider.
10. Keep existing generated Markdown unchanged.
11. Expose provenance through the document API and make frontend types nullable-compatible.
12. Keep Installation Guide generation out of this slice.

## Consequences

- a Document Version can truthfully be Source-backed, Catalog-backed, Evidence-backed, or mixed;
- future semantic generators no longer require a fabricated Source record;
- multi-evidence provenance is supported without schema churn;
- existing lifecycle/history remains intact;
- Evidence remains the owner of evidence content and materialization;
- Installation Guide generation can now be implemented as a separate, focused next slice.
