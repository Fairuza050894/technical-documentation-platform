# Architecture Portal

The Technical Documentation Platform is a modular monolith with Clean Architecture boundaries.

```text
Presentation → Application → Domain
Infrastructure → Application ports
Domain → no framework dependencies
```

## Architecture views

- [System context](system-context.md)
- [Container view](container-view.md)
- [Component view](component-view.md)
- [Domain model](domain-model.md)
- [Data and information model](data-and-information-model.md)
- [Security architecture](security-architecture.md)
- [Deployment view](deployment-view.md)
- [Architecture decision records](../decisions/)
- [Generated API surface](../_generated/api-surface.md)
- [Generated frontend route index](../_generated/frontend-route-index.md)

## Current modules

```text
workspaces
projects
features
sources
catalog
changes
documents
```

Identity and system-health capabilities are cross-cutting presentation and application concerns rather than business modules.

## Architectural principles

1. Business rules remain framework-independent.
2. Persistence, transport, storage, and identity providers are adapters.
3. Evidence is immutable, checksummed, and attributable.
4. Factual generation is deterministic.
5. Additive migrations protect existing identifiers and evidence relationships.
6. New generalization is introduced only after a repeated need is demonstrated.
7. Production-only controls are not simulated as completed capabilities.

## Current constraints

- SQLite and local artifact storage are local-development adapters.
- The source-to-document path is OpenAPI-specific.
- The frontend shell is composed through explicit app-layer components and ordered CSS layers.
- OIDC, RBAC, production migrations, deployment packaging, and observability remain planned.
