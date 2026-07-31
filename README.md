# Technical Documentation Platform

A source-backed platform for turning technical artifacts into structured catalogs, traceable changes, and generated technical documents.

## Current phase

This repository is in **MVP 1 product hardening**. The source-to-document vertical slice now supports:

1. Project and OpenAPI source management.
2. Deterministic synchronization and API catalog normalization.
3. Snapshot comparison and breaking-change classification.
4. Versioned Technical Source Overview generation.
5. Review, approval, workflow history, and version comparison.
6. A source-backed operational workspace with no demo metrics.

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


## OpenAPI Source Management slice

The Sources workspace imports OpenAPI 3.0.x and 3.1.x JSON/YAML files into an existing active project. Files are validated deterministically, stored under `.runtime/artifacts`, and represented by metadata plus a SHA-256 checksum.

API endpoints:

```text
POST /api/projects/{project_id}/sources/openapi
GET  /api/projects/{project_id}/sources
GET  /api/sources/{source_id}
POST /api/sources/{source_id}/archive
```

After applying this slice, refresh dependencies because the backend adds YAML and multipart parsing:

```bash
make bootstrap
```

Test the upload flow with `fixtures/openapi/commerce-api-v1.yaml`. Version 2 is reserved for the upcoming snapshot and change-detection slice.

Run the dedicated audit with:

```bash
make audit-sources
```


## API Catalog synchronization slice

The API Catalog workspace synchronizes an active OpenAPI source into normalized operations and component schemas. Each synchronization run is stored as a traceable snapshot linked to the source checksum and JSON Pointer evidence.

API endpoints:

```text
POST /api/sources/{source_id}/synchronizations
GET  /api/sources/{source_id}/synchronizations
GET  /api/synchronizations/{run_id}
GET  /api/projects/{project_id}/api-catalog
```

The first implementation is synchronous and local by design. The application boundary keeps the parser, repository, and artifact reader replaceable so background workers can be introduced without changing the catalog domain.

Run the dedicated audit with:

```bash
make audit-catalog
```

## Snapshot comparison and change detection

The Changes workspace compares two completed synchronization snapshots. The deterministic comparator classifies operation and schema changes as `ADDED`, `MODIFIED`, or `REMOVED`, with `NON_BREAKING`, `POTENTIALLY_BREAKING`, or `BREAKING` severity.

API endpoint:

```text
POST /api/projects/{project_id}/comparisons
```

For a local demonstration, import and synchronize both `fixtures/openapi/commerce-api-v1.yaml` and `fixtures/openapi/commerce-api-v2.yaml`, then compare their completed snapshots in **Changes**.

Run the dedicated audit with:

```bash
make audit-changes
```


## Technical Source Overview generation

The Documents workspace generates deterministic Markdown from a completed synchronization snapshot. A baseline snapshot is optional and, when selected, adds a breaking-change summary produced by the existing deterministic comparator.

Generated documents include project and source metadata, endpoint details, request and response models, component schemas, security information, JSON Pointer evidence, generation metadata, and a SHA-256 content checksum.

API endpoints:

```text
POST /api/projects/{project_id}/documents/technical-source-overview
GET  /api/projects/{project_id}/documents
GET  /api/documents/{document_id}
GET  /api/documents/{document_id}/download
```

The same normalized inputs always produce the same Markdown content. Generation time and history metadata are stored separately and do not alter the document checksum.

Run the dedicated audit with:

```bash
make audit-documents
```

## Document lifecycle core

Generated Technical Source Overviews are organized as immutable document versions. The first distinct content is version `1.0`; each later distinct checksum creates the next minor version. Generating identical normalized content reuses the existing version instead of creating a duplicate.

Lifecycle statuses:

```text
DRAFT
IN_REVIEW
CHANGES_REQUESTED
APPROVED
SUPERSEDED
```

API endpoints:

```text
GET  /api/documents/{document_id}/versions
GET  /api/document-versions/{version_id}
GET  /api/document-versions/{version_id}/download
POST /api/document-versions/{version_id}/submit-review
POST /api/document-versions/{version_id}/request-changes
POST /api/document-versions/{version_id}/approve
POST /api/document-versions/{version_id}/supersede
GET  /api/document-versions/{version_id}/workflow-events
```

Approving a newer version automatically supersedes the previously approved version in the same document series. Every generation and workflow transition records actor, status transition, comment, and timestamp. Existing rows from the previous `generated_documents` table are migrated automatically into version history when the backend starts.

Run the dedicated lifecycle audit with:

```bash
make audit-lifecycle
```


## Product UI foundation and operational overview

The application shell uses grouped navigation, persistent runtime context, dense technical
tables, semantic status colors, keyboard-visible focus states, and responsive layouts. The
Overview page assembles live data from existing project, source, synchronization, and document
APIs; it does not display fabricated metrics.

Operational Overview includes:

```text
Active projects
Ready technical sources
Completed synchronization snapshots
Pending document reviews
Attention-required conditions
Recent source and document activity
Project health
```

The previous engineering-foundation cards are available under **System status**, together with
live backend metadata and deterministic documentation policies.

Run the dedicated audit with:

```bash
make audit-product-ui
```

## Visual refinement and product polish

The application chrome and Operational Overview use a compact enterprise workbench pattern
rather than a repeated card grid. Primary navigation includes consistent inline SVG icons,
while the Overview combines a flat operational signal strip, activity stream, project health
matrix, and an action rail.

The visual system keeps native form controls and semantic HTML, but applies consistent control
height, label hierarchy, table density, status semantics, focus behavior, and responsive
navigation. No gradient, glass effect, decorative illustration, or fabricated chart is used.

Run the dedicated audit with:

```bash
make audit-visual-refinement
```

## Project-Centric Workbench

The frontend keeps workspace, project, and workflow-stage context in browser URLs. Open an
active project from the workspace Project Registry, then move through Overview, Sources, API
Catalog, Changes, and Documents without selecting the project again.

Representative routes:

```text
/workspaces/:workspaceId/projects
/workspaces/:workspaceId/projects/:projectId/workbench/overview
/workspaces/:workspaceId/projects/:projectId/workbench/sources
/workspaces/:workspaceId/projects/:projectId/workbench/catalog
/workspaces/:workspaceId/projects/:projectId/workbench/changes
/workspaces/:workspaceId/projects/:projectId/workbench/documents
```

Run the dedicated audit with:

```bash
make audit-workbench
```

## Workspace Foundation

Workspace is the persistent operational boundary above Project. The sidebar selector always
shows the active workspace; opening a project does not replace that context. Workspace Home and
Projects are scoped through canonical URLs, while legacy project routes remain readable during
the additive migration.

Existing projects are assigned to the protected `General Workspace` without changing their IDs
or any source, snapshot, comparison, document, or version relationships. Project governance is
shown as `Personal` or `Team` ownership. The previous `workspace_type` API field remains only as
a temporary compatibility field and is no longer presented as a workspace.

Workspace APIs:

```text
POST /api/workspaces
GET  /api/workspaces
GET  /api/workspaces/{workspace_id}
POST /api/workspaces/{workspace_id}/archive
POST /api/workspaces/{workspace_id}/projects
GET  /api/workspaces/{workspace_id}/projects
```

Run the dedicated audit with:

```bash
make audit-workspaces
```
