# MVP 1 — HLD Hybrid Enterprise Generation Profile

## Objective

Extend the generic enterprise generation foundation with **HLD — High Level Design** while
preserving the canonical 0010C HLD readiness contract exactly.

HLD is a hybrid document: governed technical evidence establishes the observable system boundary,
while architectural rationale may be supplied only through explicitly classified governed claims.
The generator must not manufacture architecture facts when evidence is incomplete.

## Canonical readiness contract

HLD generation eligibility comes exclusively from 0010C.

The HLD readiness profile requires:

- one governed technical Evidence Artifact — `SOURCE_ARTIFACT` or `CATALOG_SNAPSHOT` — as the
  blocking minimum; and
- an `OBSERVED` or deterministically `INFERRED` HLD-relevant Claim as a warning-level contextual
  enhancement.

Therefore a Project with valid technical evidence but no HLD claim is `PARTIALLY_READY` and remains
eligible. Semantic `USER_JOURNEY`, `DEPLOYMENT_RUNTIME`, or `UAT_RESULT` evidence alone does not
satisfy the HLD technical-evidence blocker. The generation layer still does not impose a hidden
Catalog prerequisite.

## Generation profile

Profile schema version: `enterprise-generation-profile-v2`.

HLD profile:

- profile key: `enterprise-hld-v1`;
- document type: `HLD`;
- accepted evidence kinds in the current Evidence registry: `CATALOG_SNAPSHOT`, `SOURCE_ARTIFACT`;
- rendered governed claim classifications: `OBSERVED`, `INFERRED`;
- output format: Markdown.

The existing `EnterpriseDocumentGenerationService` remains the only enterprise generation
application pipeline. HLD does not introduce a parallel service or duplicate readiness rules.

## Deterministic evidence selection

The cross-context input adapter selects the newest artifact across the profile's accepted evidence
kinds using persisted capture time, creation time, and immutable artifact identity.

Selection does not use document-type-specific branches. The selected Evidence kind determines how
the technical generation context is projected:

- `CATALOG_SNAPSHOT` resolves the existing completed synchronization, Source, normalized
  operations, and normalized schemas;
- `SOURCE_ARTIFACT` resolves the existing Source directly and does not require or invent a Catalog
  synchronization.

This means a newly imported Source can produce an eligible source-backed HLD before Catalog
normalization, exactly as the canonical readiness policy permits. If a newer governed Catalog
snapshot exists, it naturally becomes the selected richer evidence under the same deterministic
ordering.

## Provenance contract

A source-only HLD has no legitimate Catalog synchronization identifier. The platform therefore
makes `DocumentVersion.target_run_id` nullable instead of storing a sentinel or synthetic run.

The nullable provenance contract is propagated through:

- the Documents domain model;
- application DTOs and HTTP responses;
- SQLite persistence and existing-database migration;
- frontend document types and the existing version-history presentation.

Existing non-null synchronization provenance remains unchanged for Technical Source Overview, LLD,
and As-Built versions.

The SQLite migration rebuilds the existing `document_versions` table only when the current
`target_run_id` column is still `NOT NULL`, copies all version rows, recreates indexes, and preserves
document workflow history. No generated version content is rewritten.

## HLD factual boundary

The HLD renderer produces high-level architecture content rather than duplicating LLD detail.

It may render:

- Project and Workspace identity;
- selected Source identity, API metadata, checksum, and Evidence identity;
- a compact normalized API boundary when the selected evidence is a Catalog snapshot;
- `OBSERVED` HLD claims as governed direct context;
- `INFERRED` HLD claims only under an explicit Inferred label with their deterministic derivation
  reference;
- readiness warnings and remediation;
- immutable Evidence references and checksums.

When only `SOURCE_ARTIFACT` is selected, the HLD explicitly states that normalized endpoint/schema
inventory is unavailable and does not fabricate a synchronization or implementation inventory.

`UNVERIFIED` claim statements are excluded from factual sections.

## Known architecture gaps

The initial HLD profile does not infer component topology, runtime placement, infrastructure
ownership, non-functional requirements, data flows, or architecture decisions from OpenAPI alone.
Those subjects require future governed evidence or explicitly classified claims.

AI is not evidence and does not determine readiness, claim strength, or architectural truth.

## Determinism and lifecycle reuse

Generation time, random version identity, actor identity, and revision reason are not embedded in
the Markdown. Identical canonical inputs therefore produce identical Markdown and SHA-256 checksum
and reuse the existing immutable version.

HLD reuses the existing document series, minor-version progression, review/approval workflow,
download endpoints, archived mutation guard, and audit history.

## Frontend compatibility

This slice does not add an HLD generation button or redesign Documents Workspace. It only hardens
the existing document version presentation so a valid source-backed enterprise version can display
`Source evidence` when no target synchronization exists.

The frontend generated-document type contract is widened to the document types currently produced
by the platform: Technical Source Overview, HLD, LLD, and As-Built.

## Non-goals

This slice does not implement SOP, User Guide, Installation Guide, Project Handover, UAT Evidence,
Journey Map, or Developer Onboarding Brief generation. It also does not add Template CRUD, AI
drafting, new evidence collectors, browser automation, Git hosting integration, MCP, or new
frontend generation controls.

## Acceptance criteria

- HLD generation uses the existing generic enterprise generation service;
- HLD eligibility remains canonical readiness using technical evidence
  `SOURCE_ARTIFACT | CATALOG_SNAPSHOT`, with no hidden Catalog prerequisite;
- source-only governed evidence can generate an HLD with nullable synchronization provenance;
- Catalog-backed HLD can render a compact normalized API boundary;
- evidence selection is deterministic and profile-driven rather than HLD-specific in the adapter;
- observed and inferred architectural claims remain visibly distinct;
- inferred claims preserve derivation references;
- unverified claim statements are not rendered as facts;
- source-only HLD explicitly exposes missing normalized Catalog detail;
- existing document versions survive the nullable-provenance migration with workflow history;
- existing LLD, As-Built, Technical Source Overview, lifecycle, and download behavior remain
  backward compatible;
- focused tests and the full repository quality gate pass.
