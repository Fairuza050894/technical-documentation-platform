# ADR-026: Materialize Semantic Evidence Before Generation

- Status: Accepted
- Date: 2026-08-12
- Decision owners: Product Engineering and Technical Documentation

## Context

ADR-025 introduced referenced `USER_JOURNEY`, `DEPLOYMENT_RUNTIME`, and `UAT_RESULT` Evidence
Artifacts. Those records provide provenance, checksum, and an opaque content reference, but they do
not provide typed facts that a deterministic document renderer can safely consume.

If registration alone makes a document eligible, generation must either fetch arbitrary content,
invent missing facts, or fail behind a second eligibility gate. All three outcomes violate the
platform's deterministic evidence doctrine.

## Decision

1. Keep Evidence Artifact registration separate from content materialization.
2. Define `semantic-evidence-manifest-v1` with typed payloads for the three semantic Evidence kinds.
3. Canonicalize typed manifests deterministically and require their SHA-256 to equal the immutable
   Evidence Artifact checksum.
4. Persist the normalized manifest in a separate immutable `evidence_materializations` table.
5. Do not persist raw browser recordings, CI logs, screenshots, arbitrary files, or external raw
   payloads.
6. Reject direct local-file and HTTP(S) references in normalized materialized facts.
7. Reject common secret-bearing value patterns and allow deployment configuration names only,
   never configuration values.
8. Advance readiness to `document-readiness-v3`.
9. Require a matching materialization for User Guide, Journey Map, Installation Guide, and UAT
   Evidence semantic readiness.
10. Surface matching but unmaterialized Evidence Artifacts as explainable `UNMATERIALIZED`
    supporting references.
11. Do not add Installation Guide generation yet. Document version provenance still assumes a Source
    record and must be generalized separately instead of fabricated.
12. Keep AI outside evidence registration, materialization, checksum verification, and readiness.

## Consequences

- readiness remains the single deterministic eligibility source;
- opaque references cannot masquerade as renderable governed facts;
- future browser, CI/CD, repository, and UAT adapters can normalize outputs into the same typed
  materialization boundary;
- future generators can consume canonical facts without network fetches or local-file access;
- the new table is additive and does not rewrite existing Evidence Artifact or Claim history;
- document provenance generalization remains an explicit follow-up rather than being hidden inside
  Installation Guide generation.

## Follow-up

ADR-027 resolves the deferred Document Version provenance constraint by introducing append-only,
multi-reference provenance and nullable Source identity while preserving existing history.
