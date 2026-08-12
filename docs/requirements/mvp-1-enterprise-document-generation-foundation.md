# MVP 1 — Enterprise Document Generation Foundation

## Objective

Establish a generic deterministic enterprise-document generation path on top of the canonical
document registry, evidence/claims foundation, and readiness engine without replacing the existing
Technical Source Overview generator.

The first supported enterprise generation profile is **LLD — Low Level Design**.

## Why LLD is first

The current evidence model can already provide a governed `CATALOG_SNAPSHOT`. The LLD readiness
profile treats that evidence as the blocking minimum and treats governed contextual claims as a
warning-level enhancement. This permits a safe deterministic first generator without weakening the
stricter As-Built requirement for an `OBSERVED` claim.

As-Built remains unsupported by this generation slice until its stricter observed-fact path is
implemented and proven.

## Generic generation profile

Profile schema version: `enterprise-generation-profile-v2`.

The initial profile is:

- profile key: `enterprise-lld-v1`;
- document type: `LLD`;
- accepted evidence kinds: `CATALOG_SNAPSHOT`;
- compatibility primary evidence kind: `CATALOG_SNAPSHOT`;
- rendered governed claim classifications: `OBSERVED`, `INFERRED`;
- output format: Markdown.

The generation service resolves a profile by canonical `DocumentType`. Unsupported enterprise
types fail explicitly instead of silently falling back to another generator.

The v2 profile contract permits an ordered set of accepted evidence kinds so later document types
can preserve canonical readiness rules that are broader than one Catalog snapshot. The
`primary_evidence_kind` property remains a compatibility view of the first accepted kind; the
cross-context adapter selects deterministically from the full accepted set.

## Readiness gate

Generation eligibility comes exclusively from 0010C.

A request:

1. resolves the canonical enterprise document profile;
2. queries the canonical document readiness assessment;
3. stops before evidence collection or rendering when `eligible` is false;
4. returns the readiness policy version, state, blocker rules, missing inputs, and remediation;
5. proceeds only when the readiness engine reports no blocker.

The generation layer does not recreate blocker rules.

## Evidence selection

The first LLD profile selects the latest persisted `CATALOG_SNAPSHOT` Evidence Artifact
deterministically using capture time, creation time, and immutable artifact identity.

The artifact origin must still resolve to a completed Catalog synchronization for the same Project.
The corresponding Source, normalized operations, and normalized schemas are then projected into a
transport-independent generation context.

The generated version retains the existing Source and synchronization foreign-key provenance.

## Claim safety

Only Project claims explicitly relevant to `LLD` enter the generation context.

- `OBSERVED` statements may be rendered under an explicitly labelled Observed section.
- `INFERRED` statements may be rendered only under an explicitly labelled Inferred section and
  must preserve their derivation reference.
- `UNVERIFIED` statements are not rendered as factual content. The document records only how many
  such LLD-relevant statements were excluded.

AI output is not evidence and does not upgrade claim classification.

## Deterministic Markdown

The LLD renderer includes:

- document control and generation/readiness policy identity;
- Project and selected Source/Snapshot provenance;
- normalized API operations and JSON Pointer evidence;
- normalized component schemas and JSON Pointer evidence;
- governed observed and inferred contextual claims;
- readiness warnings/advisories;
- evidence checksums and references;
- known generation gaps and factual-safety policy.

Generation time, random document IDs, actor identity, and revision reason are not embedded in the
Markdown. Identical canonical inputs therefore produce identical content and SHA-256 checksum.

## Document lifecycle and versioning

This slice reuses the existing `DocumentSeries`, `DocumentVersion`, checksum duplicate protection,
minor version progression, workflow events, download endpoints, and approval lifecycle.

`DocumentVersion.create` now accepts an explicit document type while retaining
`TECHNICAL_SOURCE_OVERVIEW` as its backward-compatible default.

The current database schema already supports one document series per `(project_id, document_type)`.
No database migration is required for LLD.

## API

New governed mutation:

`POST /api/projects/{project_id}/documents/{document_type}/generate`

The initial accepted generation profile is `LLD`.

Existing document list/detail/version/download/workflow endpoints are reused unchanged.

A readiness-blocked request returns HTTP 409 with a standard error envelope plus structured
readiness details.

## Archived access

Enterprise generation is blocked for archived Projects and archived Workspaces. Existing generated
documents and versions remain readable through the established archived read-only contract.

## Non-goals

This slice does not implement:

- generators for the remaining nine enterprise document types;
- custom/system Template CRUD;
- AI drafting;
- impact/version rules beyond the existing immutable checksum/minor-version lifecycle;
- browser/Vibium collection;
- GitHub/GitLab live collection;
- Schemathesis/live conformance;
- MCP;
- frontend generation controls.

## Acceptance criteria

- generic enterprise profile and renderer ports exist;
- the Documents domain remains independent from Evidence, Readiness, Catalog, and HTTP frameworks;
- cross-context evidence/readiness collection is isolated in a Documents infrastructure adapter;
- LLD generation is blocked by canonical readiness before rendering;
- blocked responses expose canonical rule/remediation details;
- generated LLD contains normalized API/schema evidence and checksum traceability;
- observed and inferred claims remain visibly distinct;
- unverified claims never appear as confirmed factual content;
- identical canonical inputs reuse the existing immutable version;
- existing Technical Source Overview behavior remains backward compatible;
- existing document lifecycle/read/download behavior works for generated LLD;
- archived Project/Workspace mutation remains blocked;
- focused tests and the full repository quality gate pass.
