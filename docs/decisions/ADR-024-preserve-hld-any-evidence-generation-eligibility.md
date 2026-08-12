# ADR-024: Preserve HLD Any-Evidence Generation Eligibility

- Status: Accepted
- Date: 2026-08-11
- Decision owners: Product Engineering and Technical Documentation

## Context

ADR-022 created a generic enterprise generation pipeline around a profile, canonical readiness,
governed Evidence/Claims, deterministic rendering, and the existing document lifecycle. ADR-023
proved that pipeline with the stricter As-Built factual contract.

HLD is different. Its canonical 0010C readiness blocker is `ANY_EVIDENCE`, not
`CATALOG_SNAPSHOT`. The current generation input adapter, however, was originally shaped around LLD
and As-Built: one `primary_evidence_kind` was selected and always resolved as a Catalog
synchronization.

Adding HLD with `primary_evidence_kind="CATALOG_SNAPSHOT"` would therefore create a hidden
precondition stronger than readiness. Treating a source-only HLD as if it had a Catalog run would
instead require synthetic provenance. Both choices violate the platform's deterministic governance
model.

## Decision

1. Evolve the enterprise generation profile contract to
   `enterprise-generation-profile-v2` with `accepted_evidence_kinds`.
2. Retain `primary_evidence_kind` as a compatibility property returning the first accepted kind;
   it is not an additional eligibility rule.
3. Add `enterprise-hld-v1` with accepted current evidence kinds `CATALOG_SNAPSHOT` and
   `SOURCE_ARTIFACT`, and rendered claim classifications `OBSERVED` and `INFERRED`.
4. Keep 0010C as the only generation eligibility gate. No HLD blocker code is copied into the
   Documents adapter.
5. Select the newest artifact across accepted evidence kinds using capture time, creation time, and
   immutable artifact identity.
6. Project generation inputs according to the selected Evidence kind, not the requested document
   type.
7. Continue the existing Catalog projection for `CATALOG_SNAPSHOT`.
8. For `SOURCE_ARTIFACT`, resolve the Source directly and provide no target synchronization,
   operations, or schemas.
9. Make document-version target synchronization provenance nullable end to end. Do not use sentinel,
   fabricated, or unrelated synchronization identifiers.
10. Migrate existing SQLite `document_versions` tables from `target_run_id NOT NULL` to nullable
    while copying existing rows and preserving workflow history.
11. Compose HLD as a high-level boundary document. Catalog-backed HLD may summarize the normalized
    API boundary; it must not duplicate LLD operation/schema detail.
12. Render `OBSERVED` and `INFERRED` HLD claims under explicit classifications and preserve
    deterministic inference derivation references. Do not render `UNVERIFIED` statements as facts.
13. Keep `EnterpriseDocumentGenerationService` profile-neutral and unchanged in orchestration.
14. Make only the compatibility changes required in Documents Workspace to present versions with no
    synchronization reference; do not add generation controls or redesign the workspace.
15. Keep AI outside evidence, readiness, claim classification, and factual architecture generation.

## Evidence ordering decision

The adapter does not permanently prefer Catalog evidence over Source evidence. It chooses the newest
artifact across the accepted set. This prevents a stale Catalog snapshot from overriding a newer
imported Source merely because Catalog is richer.

In the ordinary ingestion sequence, the Catalog snapshot is captured after its Source and therefore
wins naturally. If a newer Source has not yet been synchronized, source-backed HLD remains valid
because canonical readiness intentionally allows it.

## Persistence consequence

`target_run_id` historically represented Catalog provenance and was non-null because all earlier
generators required a synchronization. HLD exposes that this field is optional provenance rather
than universal document identity.

The migration changes only nullability. Existing target run values, checksums, version numbers,
status, workflow events, and series pointers remain intact.

## Consequences

- HLD generation does not contradict readiness.
- Source-only HLD can be generated without fake technical provenance.
- Catalog-backed HLD still uses normalized technical evidence when available and selected.
- The generic profile model can support future evidence combinations without embedding document
  policy in the infrastructure adapter.
- Existing consumers must tolerate `target_run_id = null` for valid enterprise documents.
- The Documents UI can truthfully label those versions as source-evidence based.
- A small persistence migration is required, but no new table or parallel lifecycle is introduced.
