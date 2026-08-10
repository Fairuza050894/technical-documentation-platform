# ADR-019: Introduce an Evidence and Claims Bounded Context

- Status: Accepted
- Date: 2026-08-10
- Decision owners: Product Engineering and Technical Documentation

## Context

The platform already has several evidence-bearing records: imported source artifacts with SHA-256
checksums, immutable catalog synchronization identities, normalized API operations and schemas with
JSON Pointer provenance, and immutable document versions. These records are owned by their current
bounded contexts and should not be copied into a second raw-data store.

Enterprise document generation also needs a way to distinguish directly observed facts from
deterministic inference and unsupported statements before readiness rules can be trusted.

## Decision

1. Add a dedicated `evidence` bounded context rather than extending Sources or Documents with
   cross-cutting claim semantics.
2. Represent an Evidence Artifact as an immutable provenance manifest that references an existing
   factual origin instead of copying raw content.
3. Begin with Source Registry and completed API Catalog snapshot adapters.
4. Reuse the Source checksum for source evidence and calculate a deterministic normalized checksum
   for Catalog snapshot evidence.
5. Store Project and Workspace scope as stable cross-context references. Validate them through the
   owning repositories in the application layer.
6. Keep initial source and snapshot evidence Project-scoped. Feature scope exists in the domain for
   future Feature-specific collectors.
7. Define immutable claims as `OBSERVED`, `INFERRED`, or `UNVERIFIED`.
8. Require evidence for observed claims and evidence plus a deterministic derivation reference for
   inferred claims.
9. Keep probabilistic or AI confidence scores out of the foundation.
10. Store claim-to-document relevance in the Evidence domain as string references while validating
    those references against the canonical 0010A Document Type Registry in the application layer.
11. Expose only governed evidence-registration commands. Clients cannot submit arbitrary checksum,
    source-system, artifact-path, or provenance metadata.
12. Enforce append-only evidence and claim history with repository APIs and SQLite triggers.
13. Permit reads for archived Projects while blocking new evidence/claim mutations.

## Consequences

- Existing Source and Catalog ownership remains intact.
- Evidence provenance becomes reusable by readiness, generation, impact analysis, versioning, and
  Documentation Recovery without duplicating raw artifacts.
- Claims have explicit factual strength and cannot silently elevate inference or unsupported text to
  observed fact.
- The Evidence domain stays independent from Documents while the application layer performs the
  required governance integration.
- Readiness and generation eligibility can now be implemented as separate deterministic policies in
  0010C.
