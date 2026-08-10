# MVP 1 — Evidence and Claims Foundation

## Objective

Establish immutable evidence provenance and controlled factual claims before readiness,
generation-eligibility, impact-analysis, and enterprise document generation are implemented.

## Evidence Artifact

An Evidence Artifact is a small immutable manifest that references factual material already held by
a source system. It does not duplicate raw imported content.

The initial adapters register:

- `SOURCE_ARTIFACT` from an existing Source Registry record;
- `CATALOG_SNAPSHOT` from an existing completed normalized API synchronization.

Each artifact records Project and Workspace scope, evidence kind, source system, origin identity,
opaque content reference, collection method, collector identity, capture time, creation time, and a
SHA-256 content checksum.

Source evidence reuses the checksum established during source inspection. Catalog snapshot evidence
receives a deterministic checksum calculated from the source checksum plus normalized operations
and schemas. Random synchronization identity is excluded from the normalized checksum payload.

Registration is idempotent by evidence kind and origin identity.

## Claims

Claims are immutable statements with one classification:

- `OBSERVED`: directly supported by at least one persisted Evidence Artifact;
- `INFERRED`: supported by evidence and an explicit deterministic derivation reference;
- `UNVERIFIED`: proposed but not confirmed by sufficient evidence.

An observed claim cannot exist without supporting evidence. An inferred claim cannot exist without
both evidence and a derivation reference. Non-inferred claims cannot carry a derivation reference.

AI output is not evidence and cannot create an observed fact merely by assertion.

## Document relevance

Claims may reference zero or more canonical Project document types from the 0010A Document Type
Registry. Relevance is stored in registry order. `TECHNICAL_SOURCE_OVERVIEW` is not accepted as an
enterprise document-relevance target.

The Evidence domain stores document relevance as transport-independent string references. The
application layer validates those references against the canonical Documents registry, preventing
a direct Documents dependency inside the Evidence domain.

## Feature scope

Claims may optionally be scoped to an existing Feature/Module. A Project-level Evidence Artifact
can support a Feature-scoped claim. Evidence explicitly scoped to a different Feature cannot.

The first two evidence adapters create Project-level artifacts because imported OpenAPI sources and
catalog snapshots can support multiple Features. Future collectors may create Feature-scoped
artifacts when the evidence itself is Feature-specific.

## Immutability

Evidence artifacts, claims, claim-to-evidence references, and claim-to-document relevance are
append-only. SQLite triggers reject update and delete statements for these records.

Replacement or correction is represented by a new record. Claim supersession semantics are
deferred until a concrete versioning or review requirement needs them.

## Archived access

Archived Projects and Workspaces remain readable. New evidence registration and claim creation are
blocked when the Project or containing Workspace is archived. Claims cannot be created against an
archived Feature.

## API

Write operations are deliberately governed rather than generic:

- register evidence from an existing Source record;
- register evidence from an existing completed Catalog snapshot;
- create a Claim referencing persisted evidence.

No endpoint accepts arbitrary evidence checksum, source-system metadata, raw artifact paths, or
credential data from the client.

Read endpoints list and retrieve evidence and claims.

## Security

- credentials and tokens are not evidence metadata;
- content references are opaque application references rather than local filesystem paths;
- the domain performs no network or external fetching;
- raw imported evidence is not duplicated into the evidence tables.

## Non-goals

This slice does not implement readiness, blockers, generation eligibility, semantic truth
verification, AI confidence scoring, claim supersession, impact/version rules, browser collection,
Git collectors, live conformance, MCP, or frontend evidence management.

## Acceptance criteria

- source and completed snapshot records can be registered as immutable Evidence Artifacts;
- snapshot checksums are deterministic from normalized content;
- duplicate origin registration returns the existing Evidence Artifact;
- observed, inferred, and unverified claim invariants are domain-enforced;
- claim evidence cannot cross Project boundaries;
- document relevance accepts only 0010A enterprise document types;
- archived Project evidence and claims remain readable while mutations are blocked;
- SQLite rejects evidence/claim history update or delete;
- Evidence domain and application layers remain independent from FastAPI and SQLite;
- focused tests and the full repository quality gate pass.
