# MVP 1 — Referenced Semantic Evidence Capability

## Objective

Make the semantic evidence categories already required by document readiness available as governed,
immutable Evidence Artifacts before enabling additional enterprise document generators.

## Canonical evidence kinds

The Evidence bounded context supports five persisted kinds:

1. `SOURCE_ARTIFACT`
2. `CATALOG_SNAPSHOT`
3. `USER_JOURNEY`
4. `DEPLOYMENT_RUNTIME`
5. `UAT_RESULT`

The final three are referenced semantic evidence. They describe the nature of the governed evidence
without claiming that the platform itself produced or semantically verified the referenced
material.

## Governed reference registration

`POST /api/projects/{project_id}/evidence/references` accepts only:

- one of the three referenced semantic Evidence kinds;
- a stable origin identity;
- an opaque source reference;
- an opaque content reference;
- a SHA-256 checksum;
- a timezone-aware capture timestamp;
- optional Feature scope.

The client cannot choose `source_system` or `collection_method`. The server records
`GOVERNED_REFERENCE` and `REFERENCE_REGISTRATION`.

The endpoint contains no raw evidence payload field and rejects local `file:` references.

## Immutability and idempotency

The existing `(evidence_kind, origin_id)` identity remains canonical.

An exact registration retry returns the existing Evidence Artifact. Reusing the same kind and
origin with different Project/Feature scope, reference, checksum, capture time, or other immutable
provenance returns `EVIDENCE_ORIGIN_CONFLICT`.

No evidence table migration is required because Evidence kind, source system, and collection method
are persisted as strings and the existing append-only triggers remain valid.

## Readiness policy v2

Adding semantic kinds changes the meaning of a literal `ANY_EVIDENCE` rule. Journey or UAT evidence
must not count as the technical boundary evidence required by HLD or Developer Onboarding.

`document-readiness-v2` therefore introduces an any-of evidence-kind rule and defines:

- HLD technical evidence: `SOURCE_ARTIFACT | CATALOG_SNAPSHOT`;
- Developer Onboarding technical evidence: `SOURCE_ARTIFACT | CATALOG_SNAPSHOT`;
- User Guide journey evidence: `USER_JOURNEY`;
- Journey Map evidence: `USER_JOURNEY`;
- Installation Guide evidence: `DEPLOYMENT_RUNTIME`;
- UAT Evidence input: `UAT_RESULT`.

Readiness remains computed from canonical persisted Evidence facts and remains the source of truth.

## Security and trust boundary

Referenced evidence registration establishes immutable provenance, not semantic truth.

- raw evidence is not copied into the Evidence tables;
- credentials and tokens are not evidence metadata;
- client-controlled source-system or collection-method labels are not accepted;
- unsupported Evidence kinds cannot be registered through the referenced-evidence endpoint;
- AI is not evidence and cannot create or upgrade an Evidence Artifact;
- future browser, CI/CD, UAT, and repository collectors may call the same application contract or
  introduce specialized adapters without changing readiness semantics.

## Archived and Feature behavior

Archived Projects and Workspaces remain readable but reject new referenced evidence. Optional
Feature scope must resolve to the same active Project and follows the existing Feature mutation
guard.

## Non-goals

This slice does not implement browser/Vibium collection, CI/CD collection, UAT execution, Git
hosting integration, raw evidence upload/storage, document generation for User Guide, Installation
Guide, UAT Evidence, or Journey Map, Template CRUD, AI drafting, or MCP.

## Acceptance criteria

- all five canonical Evidence kinds round-trip through the existing repository;
- the three semantic kinds share one governed reference-registration contract;
- client source-system and collection-method spoofing is rejected;
- exact retries are idempotent and conflicting immutable provenance is rejected;
- no Evidence persistence migration is introduced;
- semantic evidence satisfies its explicit readiness rules;
- semantic evidence alone does not satisfy HLD or Developer Onboarding technical blockers;
- readiness policy identity is `document-readiness-v2`;
- archived mutation guards and append-only evidence history remain intact;
- focused tests and the full repository quality gate pass.
