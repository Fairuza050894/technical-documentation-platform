# Deployment View

| Field | Value |
|---|---|
| Document ID | TDP-ARC-007 |
| Status | Controlled draft |
| Owner | Architecture and Operations |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## Current local deployment

```mermaid
flowchart LR
DEV[Developer Workstation]
FE[Vite :4173]
BE[Uvicorn :8000]
DB[(.runtime/tdp.sqlite3)]
AR[(.runtime/artifacts)]

DEV --> FE
FE -->|proxy /api| BE
BE --> DB
BE --> AR
```

Commands:

```bash
make dev-backend
make dev-frontend
```

## CI deployment context

GitHub Actions installs locked backend and frontend dependencies and runs `make verify`. CI verifies source; it does not deploy an environment.

## Target production topology

```mermaid
flowchart LR
U[User]
GW[Gateway or Reverse Proxy]
WEB[Static Web Application]
API[Application Service]
PG[(PostgreSQL)]
OBJ[(Object Storage)]
IDP[OIDC Provider]
OBS[Logs, Metrics, Traces]

U --> GW
GW --> WEB
GW --> API
API --> PG
API --> OBJ
API --> IDP
API --> OBS
```

## Production prerequisites

- versioned schema migrations;
- immutable deployment artifact;
- environment-specific configuration and secret references;
- OIDC and authorization;
- backup and restore validation;
- liveness and readiness integration;
- monitoring, alerting, and incident ownership;
- vulnerability assessment;
- approved network and data-classification controls.

No Docker or production manifest is currently claimed as implemented.
