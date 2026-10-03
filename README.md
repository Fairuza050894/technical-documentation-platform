# Technical Documentation Platform

A source-backed engineering documentation control plane for governing product intent, technical evidence, deterministic change impact, document versions, and review decisions.

> **Current status:** enterprise-foundation MVP for controlled local development and evaluation. The repository includes governed requirements, canonical evidence primitives, repository analysis, deterministic API change impact, document lifecycle controls, and quality/security gates. It is not yet approved for public internet exposure or enterprise production use.

## Product principles

- Facts in generated documents must be traceable to source evidence.
- Business intent is revisioned; prior requirement revisions are never overwritten.
- Deterministic logic, not AI inference, controls factual generation and impact decisions.
- Missing information is reported as missing; it is never invented.
- Document content is immutable once versioned.
- Verified approvals honor separation of duties.
- Review and approval actions use a server-resolved identity boundary.
- Architecture, requirements, quality evidence, policies, and release decisions are maintained as code.

## Canonical project workflow

```text
Workspace
└── Project
    ├── Feature / Module Registry
    ├── Requirement Registry
    │   ├── Immutable revisions
    │   └── Verified Feature / Evidence / Document trace links
    ├── Source Intake
    ├── Evidence
    │   ├── Source provenance
    │   ├── Checksums
    │   ├── Materializations
    │   └── Claims
    ├── API Catalog Synchronization
    ├── Deterministic Change Detection
    ├── Deterministic Impact Assessment
    │   ├── Requirement review obligation
    │   ├── Test execution obligation
    │   └── Document review obligation
    └── Document Lifecycle
        ├── Generation
        ├── Version History
        ├── Review
        ├── Independent Approval for verified identities
        ├── Supersession
        └── Version Comparison
```

The strongest deterministic technical profile remains normalized OpenAPI/API catalog evidence. Broader repository, database, CI/CD, IaC, environment, and runtime evidence profiles remain controlled extensions.

## Repository Scanner

The Repository Scanner is an analysis subsystem that clones repositories, detects technology, executes real tests/linters/security scans, integrates with SonarQube, compares scans, and recommends documentation work. Scanner findings are advisory until promoted into canonical evidence through a governed adapter; they are not silently treated as official facts.

### Scan a repository

```bash
curl -X POST http://localhost:8000/api/scanner/scan \
  -H "Content-Type: application/json" \
  -d '{"repository_url": "https://github.com/org/repo.git", "branch": "main"}'
```

### SonarQube integration

```bash
docker compose -f docker-compose.sonarqube.yml up -d
```

```bash
SONARQUBE_URL=http://localhost:9000 \
SONARQUBE_TOKEN=<your-user-token> \
SONARQUBE_PROJECT_KEY=<your-project-key> \
PYTHONPATH=src uvicorn tdp.main:app --reload --port 8000
```

## Key governed APIs

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/workspaces/{workspace_id}/projects/{project_id}/requirements` | Create requirement revision 1 |
| GET | `/api/workspaces/{workspace_id}/projects/{project_id}/requirements` | List latest requirement revisions |
| POST | `/api/workspaces/{workspace_id}/projects/{project_id}/requirements/{id}/revisions` | Create a new immutable requirement revision |
| POST | `/api/workspaces/{workspace_id}/projects/{project_id}/requirements/{id}/trace-links` | Create a verified trace link to an existing project target |
| GET | `/api/workspaces/{workspace_id}/projects/{project_id}/requirements/traceability/coverage` | Calculate verified traceability coverage |
| POST | `/api/projects/{project_id}/comparisons` | Compare normalized API snapshots |
| POST | `/api/projects/{project_id}/comparisons/impact` | Calculate deterministic impact obligations |
| POST | `/api/scanner/scan` | Start repository analysis |
| GET | `/api/scanner/scans` | List repository scans |
| POST | `/api/scanner/scans/{id}/rescan` | Re-run analysis |
| GET | `/api/scanner/scans/{id}/compare/{other_id}` | Compare scan results |
| GET | `/api/scanner/dashboard` | Scanner operational overview |

The OpenAPI document at `/api/openapi.json` is the canonical HTTP contract for the complete API surface.

## Quick start

Prerequisites:

- Python 3.12;
- Node.js 22;
- Docker (optional, for SonarQube);
- `uv`;
- npm;
- macOS or a compatible Unix-like environment.

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

`make verify` is the merge gate. It validates generated documentation, backend lint/format/type checks, backend tests, frontend lint/tests/build, and other repository quality controls. Security scanning runs separately in CI.

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

- production OIDC configuration, role-based authorization, and workspace membership administration;
- PostgreSQL and explicit versioned database migrations;
- reproducible deployment packaging;
- approved backup, recovery, retention, and observability controls;
- complete release/export governance;
- authorized intellectual-property and licensing decision;
- formal accessibility, security, and compliance assessment.

The verified-identity approval policy already blocks author self-approval, but that control does not replace complete production RBAC and organizational separation-of-duties governance.

Repository documents may state alignment with standards, but they do not constitute certification or regulatory approval.

## Contribution and security

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
