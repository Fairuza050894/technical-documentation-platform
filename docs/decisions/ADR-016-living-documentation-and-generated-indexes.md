# ADR-016: Living Repository Documentation and Deterministic Indexes

- Status: Accepted
- Date: 2026-08-02
- Decision owners: Product Engineering and Technical Documentation

## Context

The repository contains strong patch-level requirements and ADRs, but product intent, user flows, architecture views, release governance, and control evidence are fragmented or absent. The root README has grown into a chronological implementation log. Source modules, routes, tests, and documentation can change without a deterministic freshness check.

The platform itself is intended to govern technical documentation. The repository should therefore serve as a controlled reference implementation without confusing repository documentation with future customer templates or generated project documents.

## Decision

1. Maintain one documentation portal under `docs/`.
2. Separate human-governed documents from deterministically generated indexes.
3. Generate repository inventory, ADR index, requirements index, API surface, frontend route index, test inventory, and document register through a standard-library Python script.
4. Add `make docs` and `make docs-check`.
5. Include `docs-check` in `make verify` so GitHub Actions rejects stale documentation.
6. Keep CI read-only; developers generate and review documentation locally.
7. Require controlled metadata and unique Document IDs for governance-oriented document classes.
8. Treat standards references as alignment evidence, not certification.
9. Keep repository documentation, system templates, and user-generated project documents as distinct concepts.

## Consequences

- Code and documentation changes are reviewed together.
- Generated repository facts are reproducible and do not depend on AI.
- The root README becomes concise and durable.
- Documentation structure becomes a reference for future Template Management.
- Human review remains necessary for product, risk, architecture, compliance, and approval decisions.
- The generator adds a maintenance obligation and must evolve when source structure changes.
