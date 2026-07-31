# ADR-012: Project-Centric Workbench and Browser Routing

- Status: Accepted
- Date: 2026-07-30

## Context

The product previously exposed Projects, Sources, API Catalog, Changes, and Documents as unrelated global navigation destinations. Each technical workspace loaded the project registry and maintained its own project selector. Refreshing the browser reset the active view because navigation existed only as React component state.

This made the source-to-document workflow difficult to follow and prevented stable deep links for review or collaboration.

## Decision

The frontend uses a small deterministic browser-history router with these routes:

- `/`
- `/projects`
- `/workspaces/:workspaceId/projects/:projectId/workbench/overview`
- `/workspaces/:workspaceId/projects/:projectId/workbench/sources`
- `/workspaces/:workspaceId/projects/:projectId/workbench/catalog`
- `/workspaces/:workspaceId/projects/:projectId/workbench/changes`
- `/workspaces/:workspaceId/projects/:projectId/workbench/documents`
- `/system`

Global navigation is limited to Home, Projects, and System status. Source, catalog, change, and document capabilities are stages inside a selected project.

The implementation uses the browser History API instead of adding a routing dependency. Route parsing and path construction are pure functions covered by unit tests. `popstate` updates React state so browser Back and Forward remain functional.

Existing workspace components accept an optional project prop. Standalone behavior remains available for their existing tests, while the Project Workbench supplies one persistent project and removes repeated project selectors.

A deterministic next-action resolver uses only existing project, source, synchronization, and document API facts. It does not use AI and does not invent missing state.

## Consequences

- Project context survives refresh and can be bookmarked.
- Users select a project once before moving through technical stages.
- Backend routes and persistence remain unchanged.
- Review and Release appear as planned workflow stages but do not expose non-existent functions.
- A future router library can replace the small adapter without changing project-stage URLs.
