# MVP 1 — Workspace Foundation and Context Switching

## Objective

Create a real workspace boundary above projects so one organization can separate systems,
policies, projects, and future templates without changing existing project evidence.

## Acceptance criteria

1. The system creates, lists, reads, and archives workspaces through deterministic APIs.
2. A protected `General Workspace` is created automatically.
3. Existing projects are assigned to the General Workspace without changing project IDs.
4. Existing `ENTERPRISE` project classifications migrate to `TEAM` ownership; other legacy
   classifications migrate to `PERSONAL` ownership.
5. Projects can be listed and created through workspace-scoped endpoints.
6. The legacy project endpoints remain compatible during the migration period.
7. The sidebar control is a real Workspace selector and never changes to the active project.
8. Changing workspace navigates to that workspace Home and updates the canonical URL.
9. Home and Projects show records only from the selected workspace.
10. Project Workbench routes contain both workspace ID and project ID.
11. A project cannot be opened under a workspace to which it does not belong.
12. Legacy project deep links upgrade to workspace-scoped routes after project resolution.
13. Archived workspaces remain readable and reject new governed mutations.
14. The Project form uses Ownership (`Personal` or `Team`), not `Workspace type`.
15. Generated document control metadata uses Workspace ID and Ownership terminology.
16. Workspace, project, route, migration, and context-switching behavior is covered by tests.
17. The sidebar uses an accessible custom Workspace switcher rather than a native select.
18. Workspace key and name remain visually distinct in the closed trigger and option list.
19. Archived workspaces are excluded from operational switching but remain visible in management.
20. The switcher supports click-outside, Escape, Arrow keys, Home, End, and focus restoration.
21. Workspace search appears when six or more active workspaces are available.
22. Workspace management is available from the switcher popover.
23. The audit writes one complete report to Downloads and excludes environment values,
    SQLite content, imported sources, generated documents, and secrets.

## API contract

```text
POST /api/workspaces
GET  /api/workspaces
GET  /api/workspaces/{workspace_id}
POST /api/workspaces/{workspace_id}/archive

POST /api/workspaces/{workspace_id}/projects
GET  /api/workspaces/{workspace_id}/projects
```

Existing `/api/projects` routes remain available for compatibility.

## Canonical frontend routes

```text
/workspaces
/workspaces/:workspaceId
/workspaces/:workspaceId/projects
/workspaces/:workspaceId/projects/:projectId/workbench/overview
/workspaces/:workspaceId/projects/:projectId/workbench/sources
/workspaces/:workspaceId/projects/:projectId/workbench/catalog
/workspaces/:workspaceId/projects/:projectId/workbench/changes
/workspaces/:workspaceId/projects/:projectId/workbench/documents
```

## Out of scope

- Feature or module registry.
- Requirement revision management.
- Git repository ingestion.
- Deterministic impact and semantic-version policy calculation.
- Workspace membership, roles, and authorization.
- Template inheritance and release governance.
