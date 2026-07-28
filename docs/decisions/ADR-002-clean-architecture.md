# ADR-002: Enforce Clean Architecture boundaries

- Status: Accepted
- Date: 2026-07-28

## Decision

Use four logical layers:

1. Domain
2. Application
3. Infrastructure
4. Presentation

The dependency direction always points inward. Framework-specific models stay at system boundaries.

## Consequences

- Core rules remain testable without infrastructure.
- Repository, queue, storage, and connector implementations can be replaced.
- Additional mapping code is accepted in exchange for explicit boundaries.
