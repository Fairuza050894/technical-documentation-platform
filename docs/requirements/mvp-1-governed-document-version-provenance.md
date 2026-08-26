# MVP 1 — Governed Document Version Provenance

## Objective

Allow every immutable Document Version to preserve truthful generation provenance without assuming
that a Source Registry record or API Catalog synchronization always exists.

## Provenance model

`DocumentVersion` keeps the existing `source_id`, `target_run_id`, and `baseline_run_id` fields for
backward compatibility. `source_id` and `target_run_id` are nullable.

A Document Version additionally owns an immutable ordered set of provenance references:

- `SOURCE_REGISTRY` — a legacy/technical Source Registry reference;
- `CATALOG_SYNCHRONIZATION` — a normalized API synchronization reference;
- `EVIDENCE_ARTIFACT` — a governed Evidence Artifact reference with Evidence kind and checksum.

Documents store references and checksums only. Evidence payloads and materialized manifests remain
owned by the Evidence bounded context.

## Persistence

`document_version_provenance` is append-only and keyed by Document Version plus deterministic
ordinal. Update and delete triggers reject mutation.

The migration:

1. makes `source_id` nullable while preserving the already-nullable `target_run_id`;
2. preserves every existing Document Version and workflow event;
3. backfills `SOURCE_REGISTRY` and `CATALOG_SYNCHRONIZATION` references from existing columns;
4. does not guess historical Evidence Artifact IDs that were not previously persisted.

New enterprise-generated versions persist all selected governed Evidence Artifact references in
addition to compatibility Source/Catalog references.

## API

Document summary/detail responses expose:

- nullable `source_id`;
- existing nullable `target_run_id`;
- `provenance[]` with kind, reference, optional Evidence kind, and optional checksum.

The frontend type contract accepts nullable `source_id` and the new provenance collection. There is
no visual redesign in this slice.

## Safety and compatibility

- Technical Source Overview generation remains Source/Catalog based.
- Existing LLD, As-Built, and HLD generated Markdown remains unchanged.
- Document checksum/version/review lifecycle behavior remains unchanged.
- Existing history is not rewritten.
- No cross-context Evidence payload is copied into Documents.
- Installation Guide generation remains deferred.
- AI has no role in provenance creation or validation.

## Acceptance criteria

- source-free Document Versions can be represented without fabricated identifiers;
- source/catalog legacy provenance is backfilled deterministically;
- new enterprise versions persist governed Evidence Artifact references;
- provenance rows are immutable;
- existing workflow event foreign keys and history survive migration;
- API and frontend type contracts expose generalized provenance;
- existing generators remain deterministic and backward compatible;
- focused tests and the full repository quality gate pass.

## Semantic generation follow-up

ADR-028 uses the source-free provenance model for User Guide, Installation Guide, UAT Evidence, and
Journey Map. Each generated version persists only the selected Evidence Artifact identity, kind, and
checksum in Documents provenance.
