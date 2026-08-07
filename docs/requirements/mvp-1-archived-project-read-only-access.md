# MVP 1 Archived Project Read-only Access

## Purpose

Preserve governed project knowledge after a project is archived while preventing new evidence,
capability, synchronization, and document-lifecycle mutations.

## Functional requirements

1. An archived project remains visible in its Workspace project registry.
2. The Project Registry provides an enabled **View workbench** action for archived projects.
3. Direct project workbench URLs continue to resolve archived projects.
4. Refresh, bookmark, Back, and Forward preserve archived project and stage context.
5. Project Overview, Features, Sources, API Catalog, Changes, and Documents remain readable.
6. The workbench presents an explicit read-only notice derived from project status.
7. Feature creation and archival are blocked for archived projects.
8. Source import and archival mutations are blocked for archived projects or workspaces.
9. New source synchronization is blocked for archived projects or workspaces.
10. New document generation and document workflow transitions are blocked for archived projects or
    workspaces.
11. Existing synchronization history, deterministic comparisons, document versions, workflow
    history, and evidence references remain readable.
12. Reactivation is not introduced by this requirement.

## Backend enforcement

Read-only behavior is not a frontend-only convention. Existing application services retain
server-side archived-state guards and stable error contracts for source, catalog, feature, and
document mutations. Browser controls provide user guidance but are not the security or integrity
boundary.

## Non-functional requirements

- no database schema migration;
- no new runtime dependency;
- no reactivation, RBAC, retention, purge, or legal-hold workflow;
- no CSS ownership migration or intentional redesign;
- archived-state decisions come from persisted Workspace and Project status;
- tests cover registry access, workbench resolution, stage navigation, and mutation rejection;
- repository documentation and generated indexes remain current.

## Acceptance criteria

- an archived project has an enabled **View workbench** action;
- selecting that action resolves the same project in Project Workbench;
- the workbench displays a deterministic read-only notice;
- all implemented project stages remain navigable for reading;
- existing backend archived-project mutation tests remain green;
- frontend lint, tests, production build, backend quality gates, and documentation checks pass;
- the dedicated audit writes one complete report under `~/Downloads`.
