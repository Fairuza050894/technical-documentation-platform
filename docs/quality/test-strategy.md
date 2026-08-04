# Test Strategy

| Field | Value |
|---|---|
| Document ID | TDP-QUAL-001 |
| Status | Controlled draft |
| Owner | Quality Engineering and Engineering |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## Objective

Provide confidence that domain rules, application behavior, infrastructure adapters, HTTP contracts, frontend flows, and repository documentation remain correct.

## Test layers

| Layer | Purpose | Current mechanism |
|---|---|---|
| Domain unit | Invariants and state transitions | Pytest |
| Application unit | Use cases and port behavior | Pytest |
| Infrastructure | SQLite and artifact adapters | Pytest with temporary paths |
| Presentation/API | HTTP contracts and stable errors | FastAPI TestClient |
| Architecture fitness | Dependency direction | AST-based Pytest |
| Frontend component | UI behavior and accessibility semantics | Vitest and Testing Library |
| Router | Deep links and path construction | Vitest |
| Production build | Type and bundling integrity | TypeScript and Vite |
| Repository docs | Required documents, links, metadata, freshness | Python generator and Pytest |
| Exploratory E2E | Browser workflow evidence | Planned pilot; not a replacement for stable tests |
| External API conformance | Test a documented target API | Planned, project-level, sandbox controlled |

## Test-data rules

- use synthetic, non-sensitive fixtures;
- do not commit imported customer artifacts;
- do not rely on network access in deterministic repository verification;
- isolate temporary databases and artifact stores;
- do not use production credentials or endpoints.

## Release evidence

`make verify` is the minimum repository release gate. Production readiness additionally requires security, migration, backup, deployment, and authorization evidence.
