# Technical Documentation Platform

A source-backed platform for creating, reviewing, versioning, and releasing technical documentation from verifiable engineering evidence.

> **Current status:** MVP 1 product hardening. The repository is suitable for controlled local development and evaluation. It is not approved for public internet exposure or enterprise production use.

## Product principles

- Facts in generated documents must be traceable to source evidence.
- Deterministic logic, not AI inference, controls factual generation and version decisions.
- Missing information is reported as missing; it is never invented.
- Document content is immutable once versioned.
- Review and approval actions use a server-resolved identity boundary.
- Architecture, requirements, quality evidence, and release decisions are maintained as code.

## Implemented capabilities

```text
Workspace
└── Project
    ├── Feature / Module Registry
    ├── OpenAPI Source Management
    ├── API Catalog Synchronization
    ├── Deterministic Change Detection
    └── Document Lifecycle
        ├── Generation
        ├── Version History
        ├── Review
        ├── Approval
        └── Version Comparison
```

The current generated document profile is **Technical Source Overview** from normalized OpenAPI evidence. Broader evidence types and document profiles remain roadmap items.

## Quick start

Prerequisites:

- Python 3.12;
- Node.js 22;
- `uv`;
- npm;
- macOS or a compatible Unix-like environment.

Install dependencies:

```bash
make bootstrap
```

Run the backend:

```bash
make dev-backend
```

Run the frontend in another terminal:

```bash
make dev-frontend
```

Open `http://127.0.0.1:4173`.

## Quality and documentation gates

```bash
make docs
make docs-check
make verify
make audit-docs
```

`make docs` regenerates repository-derived documentation. Review and commit the generated diff together with the related code or controlled-document change. CI runs `make verify`, which rejects stale documentation.

## Documentation portal

Start with [`docs/README.md`](docs/README.md).

Key documents:

- [Product Requirements Document](docs/product/prd.md)
- [Product vision](docs/product/product-vision.md)
- [User journeys](docs/product/user-journeys.md)
- [User flows](docs/product/user-flows.md)
- [Architecture portal](docs/architecture/README.md)
- [Security architecture](docs/architecture/security-architecture.md)
- [Test strategy](docs/quality/test-strategy.md)
- [Traceability model](docs/quality/traceability-model.md)
- [Standards applicability](docs/compliance/standards-applicability.md)
- [Release policy](docs/releases/release-policy.md)
- [External audit management response](docs/governance/external-audit-response-2026-08.md)
- [Generated document register](docs/_generated/document-register.md)

## Repository layout

```text
backend/        FastAPI modular monolith and domain modules
frontend/       React application and internal design system
docs/           Controlled project documentation
scripts/        Bootstrap, audit, and deterministic documentation automation
fixtures/       Non-sensitive test evidence
.github/        CI and repository governance
```

## Current production-readiness boundaries

The following remain required before shared production use:

- OIDC and role-based authorization;
- formal workspace membership and separation of duties;
- PostgreSQL and versioned database migrations;
- reproducible deployment packaging;
- approved backup, recovery, retention, and monitoring controls;
- authorized intellectual-property and licensing decision;
- formal security and compliance assessment.

Repository documents may state alignment with standards, but they do not constitute certification or regulatory approval.

## Contribution and security

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
