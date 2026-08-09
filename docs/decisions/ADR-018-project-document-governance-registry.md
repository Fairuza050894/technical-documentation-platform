# ADR-018: Establish a Project-Level Enterprise Document Governance Registry

- Status: Accepted
- Date: 2026-08-09
- Decision owners: Product Engineering and Technical Documentation

## Context

The Documents module has a reusable lifecycle but only one generated type,
`TECHNICAL_SOURCE_OVERVIEW`. The Features module independently contains a Feature-level
documentation-map taxonomy. The new enterprise Project taxonomy must not silently collapse those
bounded-context concepts or invalidate persisted Technical Source Overview lifecycle data.

## Decision

1. Extend the Documents `DocumentType` value space with the ten enterprise Project identifiers and
   retain `TECHNICAL_SOURCE_OVERVIEW`.
2. Define the enterprise registry in a framework-independent Documents domain governance module.
3. Exclude Technical Source Overview from enterprise checklist credit.
4. Keep the Feature/Module documentation-map taxonomy unchanged until an explicit mapping policy is
   implemented.
5. Define typed automation profiles: evidence-driven, hybrid, governed authoring, governed bundle.
6. Define `project-documentation-baseline-v1` as the deterministic default Project policy.
7. Treat checklist availability as persisted-version presence only.
8. Keep approval, evidence completeness, readiness, and generation eligibility separate.
9. Expose registry and checklist through read-only application queries and HTTP endpoints.
10. Keep static registry/policy metadata out of SQLite and out of frontend business-rule copies.

## Consequences

- Enterprise Project document identity and automation intent have one canonical source.
- Existing generated documents and SQLite rows remain backward compatible.
- No database migration is required in this slice.
- Feature documentation coverage remains stable but requires explicit Project-document mapping
  later.
- Readiness and evidence semantics can evolve without overloading checklist availability.
