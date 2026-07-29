# Technical Documentation Platform

A source-backed platform for turning technical artifacts into structured catalogs, traceable changes, and generated technical documents.

## Current phase

This repository is in **Engineering Foundation**. The first vertical slice will be:

1. Create a project.
2. Import an OpenAPI JSON/YAML file.
3. Normalize API entities.
4. Display an API catalog.
5. Compare two snapshots.
6. Generate a Technical Source Overview.

No AI-generated facts are part of the deterministic documentation pipeline.

## Local prerequisites

- macOS on Apple Silicon or Intel.
- Homebrew.
- Node.js 22.17.1.
- Python 3.12.
- `uv` package manager.

Docker, PostgreSQL, and Redis are intentionally deferred until the source-to-catalog flow requires them. This keeps the initial setup light and avoids unnecessary local resource usage.

## Bootstrap

```bash
make bootstrap
```

## Run locally

Terminal 1:

```bash
make dev-backend
```

Terminal 2:

```bash
make dev-frontend
```

Open `http://127.0.0.1:4173`.

## Verification

```bash
make verify
make audit
```

The audit command saves one complete report under `~/Downloads`.

## Repository layout

```text
backend/        FastAPI application and domain modules
frontend/       React application and internal design system
docs/           Architecture decisions and engineering standards
scripts/        Bootstrap and audit automation
```


## Project Management slice

The first business slice supports creating, listing, viewing, and archiving projects. Local project data is stored in `.runtime/tdp.sqlite3` and is not committed to Git.

After starting both services, open `http://127.0.0.1:4173` and select **Projects**.

API endpoints:

```text
POST /api/projects
GET  /api/projects
GET  /api/projects/{project_id}
POST /api/projects/{project_id}/archive
```

Run the dedicated project audit with:

```bash
make audit-projects
```
