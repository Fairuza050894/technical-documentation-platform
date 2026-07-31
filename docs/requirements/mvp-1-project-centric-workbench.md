# MVP 1 Requirement: Project-Centric Workbench

## Objective

Provide one persistent project context for the source-to-document workflow and replace object-centric global navigation with a project workbench.

## Functional requirements

1. The global sidebar exposes Home, Projects, and System status.
2. An active project can be opened from the Project Registry.
3. The selected project ID and active stage are represented in the URL.
4. Refresh, bookmark, Back, and Forward preserve or restore the route.
5. The project workbench exposes Overview, Sources, API Catalog, Changes, and Documents.
6. Review and Release are visible only as planned stages.
7. Embedded workspaces receive the selected project and do not render another project selector.
8. The project header displays project name, key, description, and status.
9. Missing project IDs produce an actionable not-found state.
10. Archived projects display an explicit archived notice.
11. The overview calculates one next recommended action from deterministic API state.
12. No backend API or database migration is required.
13. The utility bar is the single breadcrumb source inside a project workbench.
14. Truncated project context exposes the full project name through a native tooltip.
15. A superseded version without a known successor is presented as Previous version, not Replaced.

## Next-action rules

- No ready source: open Source intake.
- Ready source without completed synchronization: open API Catalog.
- Completed synchronization without a document: open Documents.
- Document in review or changes requested: continue the document workflow.
- Two or more completed snapshots: open Change analysis.
- Otherwise: continue the document lifecycle.
- Archived project: surface the read-only project state.

## Non-functional requirements

- Do not add AI-generated facts.
- Do not add a frontend routing dependency for this MVP.
- Preserve existing standalone workspace behavior and tests.
- Provide keyboard-visible focus states and responsive stage navigation.
- Keep `.env`, SQLite data, imported source artifacts, generated documents, and runtime files outside the patch and audit.

## Acceptance criteria

- `/workspaces/:workspaceId/projects/:projectId/workbench/documents` opens the selected project directly on Documents.
- The same URL remains active after browser refresh.
- Browser history events update the displayed global page or project stage.
- No project selector is rendered inside an embedded workspace.
- Existing backend quality gates pass.
- Frontend lint, tests, and production build pass.
- The workbench audit writes one report to Downloads.
- The project header does not repeat the utility-bar breadcrumb.
- A superseded version with no newer version displays Previous version and No longer current.
- The sidebar project context exposes the complete project name through its title attribute.
