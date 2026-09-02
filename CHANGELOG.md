# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Scanner Dashboard (2026-09-02)

#### Added
- **Dashboard overview page** — Grid card per repository showing health score, SonarQube score, sparkline trend, key metrics, and alerts
- **Dashboard API endpoint** — GET /scanner/dashboard returning aggregated repo summaries with score trends and auto-generated alerts
- **Score drop alerts** — Automatic detection when health score drops more than 5 points between scans
- **Security alerts** — Critical vulnerability detection from latest scan data
- **Test failure alerts** — Warning when test failure rate exceeds 20%
- **Sparkline charts** — SVG sparkline showing score trend over last 10 scans per repository
- **Dashboard navigation** — New "Dashboard" entry in sidebar navigation pointing to /scanner/dashboard
- **Dashboard CSS** — Complete styling for summary bar, alerts panel, repo grid, and repo cards



### Repository Scanner — SonarQube Integration (2026-08-31)

#### Added
- **SonarQube client** — `SonarQubeClient` with Bearer token auth, fetches project measures (bugs, vulnerabilities, code smells, coverage, ratings) and issue counts by severity
- **Dual scoring system** — Side-by-side comparison of internal health score vs SonarQube quality gate score with delta indicator
- **SonarQube comparison UI** — `SonarQubeComparison` component with rating badges (A-E), metrics grid, and issues severity bar
- **SonarQube tab** — New tab in ScannerWorkspace showing SonarQube analysis results when available
- **SonarQubeResult domain model** — Dataclass storing SonarQube metrics, ratings, issue counts, and computed scores
- **SQLite schema migration** — Auto-migration for `sonarqube_json` column in `scan_results` table
- **Docker Compose** — `docker-compose.sonarqube.yml` for local SonarQube 10.7 Community instance

### Repository Scanner — Real Analysis Pipeline (2026-08-31)

#### Changed
- **Test runner** — Uses `sys.executable` instead of hardcoded `python3` for venv-aware subprocess execution
- **Test runner** — Installs project dependencies (`pip install -e .`) before running pytest
- **Test runner** — Installs npm dependencies (`npm install`) before running jest, eslint, and npm audit
- **Test runner** — Supports `requirements/dev.txt` and `requirements/test.txt` for test dependencies
- **Linter** — Improved flake8 issue counting with line-level parsing
- **Security scanner** — Defensive JSON parsing for pip-audit and npm audit responses

### Repository Scanner — Test Suite (2026-08-31)

#### Added
- **Domain tests (26)** — ScanId, ScanResult.create, ScanResult lifecycle, ProjectHealth, TechStack, FileAnalysis, SecurityScan, TestSuite
- **Infrastructure tests (19)** — compare_scans: identical detection, health delta, file delta, issues added/removed, frameworks, tests, security, metrics, time_between formatting
- **Application tests (11)** — get_scan, list_scans, delete_scan, start_scan, rescan, ScanDto.from_domain
- **Presentation tests (9)** — All API endpoints with 404 cases
- **pytest-asyncio** — Async test support with auto mode

### Repository Scanner — Complete Module (2026-08-30)

#### Added
- **Scanner domain model** — ScanResult, ScanId, HealthLevel, TechStack, FileAnalysis, TestSuite, LintResult, SecurityScan, DocumentSuggestion, ProjectHealth, MetricDelta, ScanComparison
- **Scanner application service** — Start scan, rescan, compare, generate documents, list, get, delete
- **Git operations** — Clone repositories with branch support and temp directory management
- **File analyzer** — Count files, lines, detect languages by extension, identify config files and project artifacts
- **Tech stack detector** — Detect frameworks (Django, Flask, FastAPI, React, Next.js, Vue, Angular, Express, NestJS, Spring Boot, Gin, Echo), databases, tools, CI/CD, testing, linting
- **Health calculator** — Score calculation based on test pass rate, lint issues, security vulnerabilities, documentation artifacts
- **Test runner** — Execute pytest, jest, go test; parse results into TestSuite model
- **Linter** — Execute flake8, eslint; parse results into LintResult model
- **Security scanner** — Execute pip-audit, npm audit; parse results into SecurityScan model
- **Scan comparator** — Compare two scans with delta calculation for health, files, lines, issues, frameworks, tests, security
- **Document generator** — Suggest documents based on tech stack, file analysis, and project stage
- **Document store** — Save and retrieve generated documents with scan association
- **SQLite repository** — Persistent storage for scan results with JSON serialization
- **REST API** — POST /scanner/scan, GET /scanner/scans, GET /scanner/scans/{id}, DELETE /scanner/scans/{id}, POST /scanner/scans/{id}/rescan, GET /scanner/scans/{id}/compare/{other_id}, POST /scanner/scans/{id}/generate
- **ScannerWorkspace UI** — Grouped repository sidebar, health score ring, tab navigation (Overview, Tech Stack, Tests, Security, Documents), progress tracking
- **ScanComparisonView** — Side-by-side comparison with delta indicators, metric cards, issues diff, frameworks diff
- **MarkdownPreview** — Markdown rendering with Mermaid diagram support
- **Scanner CSS** — Complete styling for scanner workspace, history, comparison, health bars, tabs, suggestions

## [Unreleased]

### Scanner Dashboard (2026-09-02)

#### Added
- **Dashboard overview page** — Grid card per repository showing health score, SonarQube score, sparkline trend, key metrics, and alerts
- **Dashboard API endpoint** — GET /scanner/dashboard returning aggregated repo summaries with score trends and auto-generated alerts
- **Score drop alerts** — Automatic detection when health score drops more than 5 points between scans
- **Security alerts** — Critical vulnerability detection from latest scan data
- **Test failure alerts** — Warning when test failure rate exceeds 20%
- **Sparkline charts** — SVG sparkline showing score trend over last 10 scans per repository
- **Dashboard navigation** — New "Dashboard" entry in sidebar navigation pointing to /scanner/dashboard
- **Dashboard CSS** — Complete styling for summary bar, alerts panel, repo grid, and repo cards



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
