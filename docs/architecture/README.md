# Architecture Overview

The product starts as a modular monolith with Clean Architecture boundaries.

```text
Presentation -> Application -> Domain
Infrastructure -> Application ports
Domain -> no framework dependencies
```

Initial modules:

- Projects
- Sources
- Synchronization
- Technical Catalog
- Change Detection
- Documents
- Audit

The first production database will be PostgreSQL. The foundation patch deliberately does not install or configure it yet because the initial health-check slice does not persist business data.


## Implemented vertical slices

### Project Management

```text
HTTP API / React UI
        ↓
ProjectApplicationService
        ↓
ProjectRepository port
        ↓
SQLite local adapter
```

The SQLite adapter is a local MVP decision. PostgreSQL remains the intended enterprise production database.


## Source Management boundary

The source module follows the same dependency rule as Projects:

```text
presentation -> application -> domain
infrastructure -> application/domain ports
```

`DeterministicOpenApiInspector`, `LocalArtifactStore`, and `SqliteSourceRepository` are replaceable infrastructure adapters. The application service does not import FastAPI, SQLite, or PyYAML.
