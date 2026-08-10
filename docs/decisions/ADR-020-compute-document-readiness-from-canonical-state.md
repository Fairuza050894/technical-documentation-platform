# ADR-020: Compute Document Readiness from Canonical State

- Status: Accepted
- Date: 2026-08-10
- Decision owners: Product Engineering and Technical Documentation

## Context

0010A established canonical Project document types, automation profiles, and availability.
0010B established immutable evidence manifests and classified claims. The platform now needs to
explain whether enough governed input exists to begin a document workflow without conflating that
question with document existence, approval, or generation.

The frontend Project Workbench already uses operational heuristics such as ready sources and
completed snapshots. Those heuristics are useful for navigation but are not a document governance
policy and must not become the source of truth for enterprise document readiness.

## Decision

1. Introduce a dedicated `readiness` bounded context.
2. Keep its domain independent from Documents, Evidence, Projects, FastAPI, Pydantic, and SQLite.
3. Normalize cross-context Project, Evidence, Claim, and Document records into readiness facts in
   the application layer.
4. Define a static versioned policy, `document-readiness-v1`, covering all ten 0010A document types.
5. Define `NOT_READY`, `PARTIALLY_READY`, and `READY` from blocker/warning findings rather than a
   probabilistic score.
6. Define eligibility as exactly the absence of a blocker.
7. Keep 0010A availability as a separate response field.
8. Compute readiness on demand and introduce no readiness persistence.
9. Represent unsupported future evidence categories as explicit missing-input requirements rather
   than claiming Source/API evidence proves user journeys, deployment state, or UAT results.
10. Require direct `OBSERVED` claims for As-Built factual readiness; inference does not satisfy it.
11. Require approved required-document versions for Project Handover readiness.
12. Expose readiness through read-only APIs and preserve archived-Project reads.
13. Keep AI entirely outside readiness and eligibility decisions.

## Consequences

- Readiness is reproducible from canonical state and policy version.
- Frontends and future CLI/MCP adapters can consume the same backend decision contract.
- Missing inputs become actionable rule findings instead of generic "not enough information" text.
- Future evidence collectors can satisfy existing semantic evidence requirements without changing
  readiness state semantics.
- Policy changes can be versioned in code and tested before migration to a configurable policy
  registry is justified.
- 0010D can integrate readiness into Project Documentation Workbench without duplicating rules.
