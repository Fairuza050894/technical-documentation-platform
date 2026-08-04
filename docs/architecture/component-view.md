# Component View

| Field | Value |
|---|---|
| Document ID | TDP-ARC-003 |
| Status | Controlled draft |
| Owner | Architecture |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## Backend component pattern

Every business module follows:

```text
presentation
↓
application
↓
domain

infrastructure
↓
application ports and domain contracts
```

## Module responsibilities

| Module | Responsibility |
|---|---|
| Workspaces | Persistent organizational boundary |
| Projects | Project identity and governance |
| Features | Feature or module identity and documentation baseline |
| Sources | Source metadata, validation, and artifact storage |
| Catalog | Normalized API snapshots |
| Changes | Deterministic snapshot comparison |
| Documents | Generation, immutable versions, lifecycle, and comparison |

## Cross-cutting components

| Component | Responsibility |
|---|---|
| Configuration | Environment contract and safe defaults |
| Identity | Server-resolved request principal |
| HTTP middleware | Request IDs, CORS, and security headers |
| Health | Liveness and dependency readiness |
| Repository docs generator | Deterministic documentation indexes |

## Future component boundaries

```text
Evidence Acquisition
Evidence Snapshot Registry
Requirement Registry
Canonical Change Set
Impact and Version Policy
Template Registry
Document Profile Registry
Release Governance
CLI Adapter
MCP Adapter
```

New adapters must reuse application services and must not duplicate domain rules.
