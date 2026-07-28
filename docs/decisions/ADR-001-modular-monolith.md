# ADR-001: Use a modular monolith

- Status: Accepted
- Date: 2026-07-28

## Context

The MVP needs strong domain boundaries without the operational cost of multiple independently deployed services.

## Decision

Use one deployable backend organized into explicit business modules. Modules communicate through public application contracts and domain events.

## Consequences

- Local development remains simple.
- Transaction boundaries remain manageable.
- Modules can later be extracted only when operational evidence justifies it.
- Architecture tests must prevent accidental cross-module coupling.
