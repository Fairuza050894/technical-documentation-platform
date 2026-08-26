# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Phase 2: Core Product Quality — Week 2 (2026-08-27)

#### Added
- **Document workspace tab navigation** — Refactored DocumentsWorkspace from single scrollable page to three tabs: Generate, Versions, Compare
- **Print stylesheet** — `@media print` rules in `application-shell.css` that hide navigation, forms, sidebar, and controls for clean printed output
- **Sidebar collapse toggle** — Collapsible sidebar with icon-only mode, persisted to `localStorage` via `tdp.sidebar-collapsed` key, smooth 0.2s CSS transition
- **ARIA main landmark label** — `<main>` element in AppShell labeled as "Main content" for screen reader navigation
- **ARIA loading state roles** — Added `role="status"` to loading indicators in SourceWorkspace, ApiCatalogWorkspace, and FeatureWorkspace

#### Changed
- `AppSidebar.tsx` — Navigation items always render (icons visible when collapsed, labels hidden)
- `application-shell.css` — Sidebar uses `flex-direction: column` with `margin-top: auto` on collapse toggle

### Phase 2: Core Product Quality — Week 1 (2026-08-27)

#### Added
- **React Error Boundary** — Root-level `ErrorBoundary` class component in `main.tsx` that catches rendering crashes and shows recovery UI with reload button
- **ConfirmDialog component** — Reusable `<ConfirmDialog>` using native `<dialog>` element with `showModal()`, backdrop styling, and configurable variant (primary/danger)
- **Workflow confirmation dialogs** — Approve and supersede document version actions now require explicit confirmation via ConfirmDialog before execution
- **Skip-to-content link** — Accessible skip link in AppShell, visually hidden until focused, jumps to `#main-content`
- **List filtering — Sources** — Text search input in SourceWorkspace filtering by name, file name, and API title
- **List filtering — Documents** — Text search input in DocumentsWorkspace version history filtering by title, status, and author
- **List filtering — Catalog** — Text search inputs in ApiCatalogWorkspace for both operations (method, path, summary) and schemas (name, type)
- **List filtering — Features** — Text search input in FeatureWorkspace filtering by name, key, kind, owner, and description
- **Danger button CSS class** — `.button--danger` style for destructive action buttons with red background
- **List filter CSS class** — `.list-filter` layout for search input + count indicator

#### Changed
- `ProjectWorkbench.tsx` — Removed planned stages 7 (Review) and 8 (Release) from stage navigation
- `DocumentsWorkspace.tsx` — WorkflowActions component now uses `useState` for pending action and renders ConfirmDialog for approve/supersede

#### Fixed
- `features/presentation/http/router.py` — Feature error handler response key changed from `request_id` to `requestId` for consistency with centralized error handlers

### Phase 1: Backend Foundation (completed prior)

#### Architecture
- Modular monolith with hexagonal architecture (ports and adapters) per bounded context
- 10 bounded contexts: Workspace, Project, Source, Catalog, Changes, Feature, Evidence, Document, Readiness, Audit
- All service, router, error handler, and wiring complete in `main.py`

#### Security
- OIDC and JWT authentication with token blacklist
- CSRF protection middleware
- Rate limiting middleware
- Security headers (HSTS, CSP, X-Frame-Options)
- Structured audit logging with request ID correlation
- RBAC authorization policy with workspace membership

#### Infrastructure
- SQLite persistence for all repositories
- Local filesystem artifact storage
- Deterministic OpenAPI parsing and catalog synchronization
- Immutable document versioning with content-addressable checksums
