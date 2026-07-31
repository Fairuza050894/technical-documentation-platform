# ADR-013: Workspace Boundaries and Additive Project Migration

## Status

Accepted.

## Context

The sidebar previously used the word `Workspace` for a display-only context that changed to the
active project. The project model also stored `workspace_type` with values `DEMO`, `PERSONAL`,
and `ENTERPRISE`. That field describes ownership or governance, not a real workspace boundary.

The product needs one workspace to contain multiple projects while preserving all existing
project-scoped sources, snapshots, comparisons, documents, and version history.

## Decision

Introduce Workspace as a first-class aggregate with a stable UUID, key, name, description,
status, and timestamps. Projects reference a workspace through `workspace_id`. Project
governance is represented by `ownership_type` with `PERSONAL` and `TEAM` values.

Existing projects are migrated additively to a deterministic `General Workspace`. The SQLite
migration adds columns instead of rebuilding the `projects` table because multiple existing
tables reference project IDs. Existing project IDs and every downstream foreign-key relation
remain unchanged.

The legacy `workspace_type` column and response field remain temporarily for compatibility.
New UI and workspace-scoped APIs use `workspace_id` and `ownership_type`; new code must not use
`workspace_type` as a workspace selector.

Canonical frontend routes are workspace-scoped:

- `/workspaces/:workspaceId`
- `/workspaces/:workspaceId/projects`
- `/workspaces/:workspaceId/projects/:projectId/workbench/:stage`

Legacy project routes remain readable and are upgraded to the canonical route after the project
is resolved.

Archiving a workspace keeps evidence readable and prevents new project, source,
synchronization, and document-lifecycle mutations.

## Consequences

- The sidebar selector always represents Workspace, never Project.
- Selecting a workspace resets navigation to that workspace Home.
- Projects are listed and created within the selected workspace.
- Project, source, catalog, change, and document identifiers remain stable.
- Application services validate workspace state because the additive SQLite migration does not
  rebuild existing foreign-key tables.
- Removing the deprecated `workspace_type` column is deferred to a dedicated schema-hardening
  migration after compatibility consumers are retired.
