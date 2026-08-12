# MVP 1 — Document Readiness and Missing Information

## Objective

Compute deterministic, explainable readiness for each canonical Project document type using the
0010A governance registry and 0010B evidence/claim foundation. This slice does not generate
enterprise documents.

## Availability is not readiness

Availability remains the 0010A lifecycle fact:

- `MISSING`: no persisted governed version exists;
- `AVAILABLE`: at least one persisted governed version exists.

Readiness is a computed policy assessment of whether sufficient governed inputs exist for a
document workflow. A document can therefore be `MISSING` and `READY`, or `AVAILABLE` and
`NOT_READY`. Readiness does not imply approval, publication, or semantic correctness.

## States

- `NOT_READY`: at least one `BLOCKER` is present.
- `PARTIALLY_READY`: no blocker is present, but at least one `WARNING` remains.
- `READY`: neither blocker nor warning remains.

`ADVISORY` findings do not downgrade readiness.

`eligible` is a deterministic projection of blockers only. `NOT_READY` is not eligible;
`PARTIALLY_READY` and `READY` are eligible for a later governed drafting/generation workflow.

## Findings

Every finding exposes:

- stable `rule_code`;
- document type;
- `BLOCKER`, `WARNING`, or `ADVISORY`;
- explanation;
- machine-readable missing-input reference;
- remediation guidance;
- supporting references when insufficient evidence/claims/documents already exist.

No probabilistic score or AI judgment participates in the state calculation.

## Policy version

The current policy is `document-readiness-v2`.

Version 2 preserves the existing document semantics while narrowing technical-evidence rules so
new semantic evidence cannot accidentally satisfy HLD or Developer Onboarding requirements.

The policy defines profiles for all ten 0010A enterprise document types in canonical registry
order. Profile coverage is locked by automated tests.

## Current evidence capability

The governed Evidence registry currently provides:

- `SOURCE_ARTIFACT`;
- `CATALOG_SNAPSHOT`;
- `USER_JOURNEY`;
- `DEPLOYMENT_RUNTIME`;
- `UAT_RESULT`.

`USER_JOURNEY`, `DEPLOYMENT_RUNTIME`, and `UAT_RESULT` are immutable referenced provenance
manifests. They satisfy only readiness rules that explicitly request those semantic kinds.

HLD and Developer Onboarding require one of the technical kinds `SOURCE_ARTIFACT` or
`CATALOG_SNAPSHOT`; user-journey, deployment, or UAT evidence alone must not satisfy those
technical-evidence blockers.

## Initial profile semantics

- HLD: requires technical evidence; missing governed architecture context is a warning.
- LLD: requires a normalized Catalog snapshot; missing governed implementation context is a warning.
- As-Built: requires a Catalog snapshot and an `OBSERVED` As-Built claim.
- SOP: requires an `OBSERVED` SOP-relevant operational claim.
- User Guide: requires validated user-journey evidence.
- Installation Guide: requires deployment/runtime evidence.
- Project Handover: requires approved HLD, LLD, As-Built, SOP, User Guide, and Installation Guide.
- UAT Evidence: requires UAT execution evidence.
- Journey Map: requires validated user-journey evidence.
- Developer Onboarding Brief: requires technical evidence; missing governed context is a warning.

`INFERRED` claims may satisfy only rules that explicitly allow them. They never satisfy the
As-Built observed-fact rule. `UNVERIFIED` claims never satisfy confirmed factual requirements.

## Computation and persistence

Readiness is computed on demand from canonical persisted Project, Evidence, Claim, and Document
state. No readiness table or assessment snapshot is introduced, preventing stale policy results.

The readiness domain consumes normalized facts and does not import Documents, Evidence, Projects,
FastAPI, Pydantic, or SQLite. Cross-context adaptation occurs in the application layer.

## API

Read-only endpoints:

- `GET /api/projects/{project_id}/readiness`
- `GET /api/projects/{project_id}/readiness/{document_type}`

Archived Projects remain readable.

## AI boundary

AI is not evidence, cannot remove blockers, cannot upgrade claim classification, and does not
participate in readiness or eligibility decisions.

## Non-goals

This slice does not implement enterprise document generation, templates, readiness persistence,
impact/versioning rules, AI drafting, frontend workbench redesign, browser collection, Git
collectors, live conformance, or MCP.

## Acceptance criteria

- all ten canonical document types have a versioned readiness profile;
- readiness and 0010A availability remain distinct fields;
- blockers deterministically produce `NOT_READY`;
- warnings without blockers produce `PARTIALLY_READY`;
- no blockers/warnings produce `READY`;
- eligibility is exactly the absence of blockers;
- As-Built inference does not substitute for observed evidence-backed claims;
- semantic evidence satisfies only explicitly matching evidence-kind rules;
- technical-evidence profiles are not unlocked by journey, deployment, or UAT evidence alone;
- Project Handover requires approved required-document versions;
- project summary exposes ready/partial/not-ready and required-policy totals;
- archived Project readiness remains readable;
- no readiness persistence is introduced;
- focused tests and the full repository quality gate pass.
