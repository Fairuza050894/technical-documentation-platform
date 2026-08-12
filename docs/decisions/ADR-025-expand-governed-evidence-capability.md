# ADR-025: Expand Governed Evidence Capability Before More Generators

- Status: Accepted
- Date: 2026-08-12
- Decision owners: Product Engineering and Technical Documentation

## Context

The initial Evidence bounded context intentionally supported only Source Registry artifacts and
normalized API Catalog snapshots. Readiness already expressed future semantic requirements for user
journeys, deployment/runtime state, and UAT execution.

Those semantic requirements cannot safely power document generation until they can exist as
immutable provenance records.

Adding the new kinds also exposes a policy problem: the original HLD and Developer Onboarding rules
used literal `ANY_EVIDENCE`. Once semantic evidence exists, a user journey alone would satisfy that
technical blocker even though the HLD generation profile accepts only Source or Catalog technical
evidence. That would create a secondary generation gate and make readiness cease to be the source
of truth.

## Decision

1. Add `USER_JOURNEY`, `DEPLOYMENT_RUNTIME`, and `UAT_RESULT` as first-class `EvidenceKind` values.
2. Keep existing `SOURCE_ARTIFACT` and `CATALOG_SNAPSHOT` behavior unchanged.
3. Register the three new kinds through one governed referenced-evidence application command and
   HTTP endpoint.
4. Accept provenance manifest metadata only; do not accept raw evidence payloads.
5. Fix referenced evidence source-system and collection-method values server-side as
   `GOVERNED_REFERENCE` and `REFERENCE_REGISTRATION`.
6. Retain `(evidence_kind, origin_id)` as immutable identity. Exact retries are idempotent;
   conflicting immutable provenance returns a conflict.
7. Reuse the existing Evidence SQLite schema and append-only triggers; introduce no migration.
8. Advance readiness policy identity to `document-readiness-v2`.
9. Add an any-of evidence-kind rule and use it for HLD and Developer Onboarding technical evidence,
   restricted to `SOURCE_ARTIFACT` and `CATALOG_SNAPSHOT`.
10. Keep User Guide, Journey Map, Installation Guide, and UAT Evidence rules bound to their exact
    semantic Evidence kinds.
11. Keep readiness computed from persisted Evidence facts with no readiness persistence.
12. Keep AI outside Evidence creation, classification, and readiness eligibility.

## Consequences

- semantic evidence can satisfy existing readiness rules without document generators fabricating
  missing inputs;
- HLD generation and readiness remain aligned as the Evidence taxonomy grows;
- future browser, CI/CD, and UAT adapters have a stable Evidence application contract without
  coupling the Evidence domain to those technologies;
- referenced evidence records provenance but does not itself prove semantic correctness;
- access-control hardening can evolve independently from the Evidence kind and readiness contracts.
