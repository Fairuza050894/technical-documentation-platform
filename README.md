# Technical Documentation Platform

A source-backed engineering documentation control plane for requirements, evidence, change impact, document governance, and release workflow.

> **Current status:** MVP 1 enterprise-foundation hardening + Repository Scanner with SonarQube integration. The repository is suitable for controlled local development and evaluation. It is not approved for public internet exposure or enterprise production use.

## Product principles

- Facts in generated documents must be traceable to source evidence.
- Deterministic logic, not AI inference, controls factual generation, impact, and version decisions.
- Missing information is reported as missing; it is never invented.
- Requirement revisions, evidence snapshots, and document versions are immutable.
- Review and approval actions use a server-resolved identity boundary.
- Workflow transitions are explicit and auditable.
- Architecture, requirements, quality evidence, and release decisions are maintained as code.

## Implemented capabilities

```text
Workspace
├── Projects
│   ├── Feature / Module Registry
│   ├── Requirement Registry
│   │   ├── Immutable revisions
│   │   └── Trace links to feature/evidence/test/document/release/source
│   ├── Sources & Evidence
│   │   ├── OpenAPI Source Management
│   │   ├── API Catalog Synchronization
│   │   ├── Canonical Evidence Artifacts
│   │   └── Governed Claims
│   ├── Deterministic Change Detection
│   ├── Deterministic Impact Assessment
│   │   └── Documentation / Testing / Architecture / Release / Security
│   ├── Governance Workflow
│   │   └── Open → Analysis → Update → Review → Approval → Release
│   └── Document Lifecycle
│       ├── Generation
│       ├── Version History
│       ├── Review
│       ├── Approval
│       └── Version Comparison
├── Governance control plane
├── Templates
└── Repository Scanner
    ├── Git Clone & Analysis
    ├── Tech Stack Detection
    ├── Real Test Execution (pytest, jest, go test)
    ├── Real Linting (flake8, eslint)
    ├── Real Security Scanning (pip-audit, npm audit)
    ├── Health Score Calculation
    ├── SonarQube Integration (dual scoring)
    ├── Scan Comparison (delta analysis)
    ├── Document Suggestions
    └── Document Generation
```

The current canonical generated document profile is **Technical Source Overview** from normalized OpenAPI evidence. Template management is implemented; broader evidence-to-document profile rules remain roadmap work.

The **Governance** workspace gives a project-scoped control surface for requirement coverage, trace links, deterministic impact decisions, and human-accountable workflow cases. It is intentionally separate from AI inference: policy decides affected control areas, while people own review and approval.

The **Repository Scanner** clones repositories, analyzes code structure, runs real tests/linters/security scanners, integrates with SonarQube for dual scoring, and generates document suggestions based on detected tech stack and project stage. Scanner evidence is not yet automatically promoted into canonical project evidence; that remains a pilot-readiness item.

## Repository Scanner

The scanner module analyzes repositories and provides health scoring with optional SonarQube integration.

### Scan a repository

```bash
curl -X POST http://localhost:8000/api/scanner/scan \
  -H "Content-Type: application/json" \
  -d '{"repository_url": "https://github.com/org/repo.git", "branch": "main"}'
```

### SonarQube integration

Start SonarQube locally:

```bash
docker compose -f docker-compose.sonarqube.yml up -d
```

Start the backend with SonarQube environment variables:

```bash
SONARQUBE_URL=http://localhost:9000 \
SONARQUBE_TOKEN=<your-user-token> \
SONARQUBE_PROJECT_KEY=<your-project-key> \
PYTHONPATH=src uvicorn tdp.main:app --reload --port 8000
```

The scanner will automatically fetch SonarQube metrics and display a dual scoring comparison (Internal Score vs SonarQube Score) in the UI.

## Governance API

Core endpoints added for the enterprise governance chain:

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/projects/{project_id}/requirements` | Create immutable requirement revision 1 |
| GET | `/api/projects/{project_id}/requirements` | List latest requirement revisions |
| POST | `/api/requirements/{requirement_id}/revisions` | Add a new immutable revision |
| POST | `/api/projects/{project_id}/trace-links` | Link a requirement to governed implementation/evidence targets |
| GET | `/api/projects/{project_id}/traceability` | Read traceability coverage |
| POST | `/api/projects/{project_id}/impact-assessments` | Apply deterministic impact policy |
| POST | `/api/projects/{project_id}/workflow-cases` | Open a human workflow case from an impact decision |
| POST | `/api/workflow-cases/{case_id}/transitions` | Advance through allowed workflow gates |
| GET | `/api/projects/{project_id}/governance-summary` | Read the project governance control-plane summary |

## Quick start

Prerequisites:

- Python 3.12;
- Node.js 22;
- Docker (optional, for SonarQube);
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

- production OIDC/RBAC enforcement and formal separation of duties;
- PostgreSQL and versioned database migrations;
- reproducible deployment packaging;
- approved backup, recovery, retention, and monitoring controls;
- automatic scanner-to-canonical-evidence ingestion with trust policy;
- formal accessibility validation;
- authorized intellectual-property and licensing decision;
- formal security and compliance assessment.

Repository documents may state alignment with standards, but they do not constitute certification or regulatory approval.

## Contribution and security

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
