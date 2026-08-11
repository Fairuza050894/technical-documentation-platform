# MVP 1 — As-Built Enterprise Generation Profile

## Objective

Extend the generic enterprise generation foundation with **As-Built Documentation** as the second
supported enterprise profile without introducing a document-specific application service.

## Profile

Generation profile:

- profile key: `enterprise-as-built-v1`;
- document type: `AS_BUILT`;
- primary evidence kind: `CATALOG_SNAPSHOT`;
- factual rendered claim classification: `OBSERVED`;
- output format: Markdown.

The existing `EnterpriseDocumentGenerationService` remains the only enterprise generation
application pipeline.

## Canonical readiness gate

As-Built generation relies exclusively on the 0010C readiness profile.

Generation requires:

1. a governed `CATALOG_SNAPSHOT`; and
2. an `OBSERVED` Claim explicitly relevant to `AS_BUILT`.

An `INFERRED` or `UNVERIFIED` claim cannot satisfy the observed-fact rule. When the readiness
assessment contains a blocker, generation stops before input collection and rendering and returns
the canonical readiness finding and remediation.

The generation layer does not reproduce the observed-claim rule.

## Factual content boundary

The As-Built draft may state as implementation facts only:

- normalized API operations and schemas from the selected Catalog snapshot;
- source and synchronization provenance;
- `OBSERVED` claims explicitly relevant to `AS_BUILT`;
- immutable evidence references and checksums.

The first As-Built profile does not render `INFERRED` or `UNVERIFIED` claim statements as factual
content.

For auditability, non-observed claims may be represented only by claim identity, classification,
and an explicit statement that they were excluded from factual As-Built content.

The draft must not invent deployment topology, infrastructure/runtime configuration, database
topology, operational procedures, user journeys, or environment configuration.

## Deterministic Markdown

The document contains:

- document control and generation/readiness policy identity;
- scope and evidence boundary;
- observed implementation assertions;
- normalized API implementation inventory;
- readiness findings;
- evidence traceability;
- excluded non-observed claim references;
- known gaps and generation policy.

Random IDs generated for the document version, generation time, actor identity, and revision reason
are not embedded into Markdown. Identical canonical inputs therefore produce identical content and
reuse the existing immutable version.

## Existing lifecycle reuse

As-Built uses the same `DocumentSeries`, `DocumentVersion`, SHA-256 duplicate protection, minor
version progression, review/approval workflow, download endpoints, and archived read-only behavior.

No new persistence table or schema migration is introduced.

## Backward compatibility

Technical Source Overview generation, LLD generation, canonical readiness, Evidence/Claim
invariants, and document lifecycle APIs remain unchanged.

## Non-goals

This slice does not implement HLD, SOP, User Guide, Installation Guide, Project Handover, UAT
Evidence, Journey Map, or Developer Onboarding Brief generation. It also does not add Template
CRUD, AI drafting, new evidence collectors, browser automation, Git hosting integration, MCP, or
frontend generation controls.

## Acceptance criteria

- the generic profile registry contains LLD and AS_BUILT;
- the same enterprise generation service handles both profiles;
- the cross-context input adapter remains profile-neutral;
- inferred-only As-Built input is rejected by canonical readiness;
- observed As-Built claims are rendered with claim/evidence traceability;
- inferred and unverified As-Built statements are absent from factual content;
- non-observed claim identities remain auditable as excluded references;
- normalized API operations and schemas retain source pointers;
- identical As-Built inputs reuse the immutable version;
- existing LLD and Technical Source Overview behavior remain unchanged;
- full repository quality gates pass.
