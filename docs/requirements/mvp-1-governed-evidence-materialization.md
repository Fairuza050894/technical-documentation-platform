# MVP 1 — Governed Evidence Materialization

## Objective

Turn referenced semantic Evidence Artifacts into deterministic, typed, checksum-verifiable facts
that later document generators can consume without fetching arbitrary URLs, reading local files, or
inventing content.

## Boundary

Evidence registration and materialization are distinct:

- `EvidenceArtifact` remains immutable provenance metadata;
- `EvidenceMaterialization` is an immutable normalized projection of the referenced evidence;
- raw source payloads remain external and are not copied into the Evidence tables;
- materialization does not upgrade Claim classification or assert facts beyond supplied typed data.

## Canonical manifest

The initial schema is `semantic-evidence-manifest-v1`.

The envelope contains `schema_version`, `kind`, and a kind-specific `payload`.

Supported typed payloads are:

- `USER_JOURNEY`: journey name, actors, preconditions, ordered user/system steps, outcomes, and
  source references;
- `DEPLOYMENT_RUNTIME`: environment, runtime components and versions, prerequisites, configuration
  key names, ordered deployment instructions, verification checks, and rollback references;
- `UAT_RESULT`: run reference, timezone-aware execution time, scenarios, statuses, expected/actual
  results, and evidence references.

Configuration values, passwords, tokens, private keys, authorization values, direct `file:`
references, and direct HTTP(S) retrieval are outside this contract.

## Checksum contract

The semantic manifest is normalized and serialized as deterministic JSON with stable key ordering.
Its SHA-256 must equal the immutable checksum already registered on the Evidence Artifact.

A mismatch returns `EVIDENCE_MATERIALIZATION_CHECKSUM_MISMATCH`; the platform does not rewrite the
Evidence Artifact checksum.

## Persistence

Materializations are stored in an additive `evidence_materializations` table keyed one-to-one by
Evidence Artifact ID. The table stores only the canonical typed manifest and materialization
metadata. Immutable update/delete triggers protect the record.

Existing Evidence Artifact and Claim rows are not migrated or rewritten.

## Readiness policy v3

`document-readiness-v3` introduces `MATERIALIZED_EVIDENCE_KIND`.

The following blockers require a matching materialized semantic Evidence Artifact:

- User Guide → `USER_JOURNEY`;
- Journey Map → `USER_JOURNEY`;
- Installation Guide → `DEPLOYMENT_RUNTIME`;
- UAT Evidence → `UAT_RESULT`.

An unmaterialized artifact remains visible in readiness findings as an `UNMATERIALIZED` supporting
reference. This keeps readiness as the only eligibility source instead of deferring content
availability to a hidden generator check.

HLD, LLD, As-Built, SOP, Project Handover, and Developer Onboarding otherwise retain their existing
readiness semantics.

## Generator boundary

Installation Guide generation is deliberately not introduced in this slice. The current document
version provenance still requires a Source record, while semantic deployment evidence does not
necessarily originate from Source Registry or API Catalog.

The next generator slice must generalize document provenance truthfully rather than inventing a
Source ID or silently requiring unrelated technical evidence.

## Acceptance criteria

- all three semantic Evidence kinds produce deterministic typed canonical manifests;
- manifest checksum must match the registered Evidence Artifact checksum;
- materialization is immutable and exact retries are idempotent;
- conflicting materialization does not replace history;
- unsupported fields, secret-like values, and direct file/HTTP references are rejected;
- raw evidence payloads are not persisted;
- registered-but-unmaterialized semantic evidence does not satisfy readiness;
- materialized semantic evidence satisfies only its matching readiness rules;
- readiness policy identity is `document-readiness-v3`;
- no enterprise document generator is added;
- no AI, browser, external HTTP resolver, CI/CD integration, MCP, or frontend authoring UI is added;
- focused tests and the complete repository quality gate pass.
