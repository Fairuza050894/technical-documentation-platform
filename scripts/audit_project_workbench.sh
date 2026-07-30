#!/usr/bin/env bash

set -u

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
REPORT_PATH="${HOME}/Downloads/technical-documentation-platform_project_workbench_${TIMESTAMP}.txt"

mkdir -p "${HOME}/Downloads"
cd "${PROJECT_ROOT}"

run_section() {
  local title="$1"
  shift

  printf '\n--- %s ---\n' "${title}"
  "$@"
  local exit_code=$?
  printf '[exit_code=%s]\n' "${exit_code}"
  return 0
}

{
  printf '%s\n' '============================================================'
  printf '%s\n' 'PROJECT-CENTRIC WORKBENCH AND PERSISTENT CONTEXT AUDIT'
  printf '%s\n' '============================================================'
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "${PROJECT_ROOT}"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"

  run_section "Git status" git status --short --branch
  run_section "Whitespace" git diff --check
  run_section "Workbench inventory" find \
    frontend/src/app \
    frontend/src/modules/workbench \
    frontend/src/modules/projects \
    frontend/src/modules/sources \
    frontend/src/modules/catalog \
    frontend/src/modules/changes \
    frontend/src/modules/documents \
    -type f -not -path '*/__pycache__/*' -print
  run_section "Persistent route contract" grep -nE \
    'projectRoutePattern|parseRoute|projectStagePath|popstate|pushState|replaceState' \
    frontend/src/app/router.ts frontend/src/app/App.tsx
  run_section "Project stage contract" grep -nE \
    'overview|sources|catalog|changes|documents|Review|Release|Project workflow' \
    frontend/src/modules/workbench/ProjectWorkbench.tsx
  run_section "Deterministic next action" grep -nE \
    'resolveNextAction|Import the first technical source|Create the first normalized snapshot|Generate the first document version|Continue document review|Review source changes' \
    frontend/src/modules/workbench/ProjectWorkbench.tsx
  run_section "Embedded project context" grep -nE \
    'project\?:|embedded\?:|!project &&|!embedded &&' \
    frontend/src/modules/sources/SourceWorkspace.tsx \
    frontend/src/modules/catalog/ApiCatalogWorkspace.tsx \
    frontend/src/modules/changes/ChangesWorkspace.tsx \
    frontend/src/modules/documents/DocumentsWorkspace.tsx
  run_section "Global navigation is project-centric" grep -nE \
    'id: "Home"|id: "Projects"|id: "System status"|ProjectWorkbench|onOpenProject' \
    frontend/src/app/App.tsx frontend/src/modules/projects/ProjectWorkspace.tsx
  run_section "No technical global navigation" bash -c \
    "! grep -nE 'id: \"Sources\"|id: \"API Catalog\"|id: \"Changes\"|id: \"Documents\"' frontend/src/app/App.tsx"
  run_section "Workbench visual language" grep -nE \
    'project-stage-navigation|next-action-panel|project-summary-grid|project-workflow-map|project-workbench-state' \
    frontend/src/styles/globals.css
  run_section "Single breadcrumb source" bash -c \
    "! grep -n 'className=\"text-action\" onClick={onBackToProjects}' frontend/src/modules/workbench/ProjectWorkbench.tsx"
  run_section "Project context tooltip" grep -n 'title={contextLabel}' \
    frontend/src/app/App.tsx
  run_section "Lifecycle presentation language" grep -nE \
    'Previous version|Replaced by v|No longer current' \
    frontend/src/modules/documents/DocumentsWorkspace.tsx
  run_section "Routing and refinement tests" grep -nE \
    'persistent project stage routes|deep link|browser history events|Project not found|neutral label|title.*Documentation Platform' \
    frontend/src/app/router.test.ts \
    frontend/src/app/App.test.tsx \
    frontend/src/modules/workbench/ProjectWorkbench.test.tsx \
    frontend/src/modules/documents/DocumentsWorkspace.test.tsx
  run_section "Ruff" uv run --project backend ruff check backend
  run_section "Ruff formatting" uv run --project backend ruff format --check backend
  run_section "Mypy" uv run --project backend mypy backend/src
  run_section "Backend tests" uv run --project backend pytest backend/tests
  run_section "ESLint" npm --prefix frontend run lint
  run_section "Vitest" npm --prefix frontend run test
  run_section "Production build" npm --prefix frontend run build

  printf '\nSafety: .env, SQLite data, runtime artifacts, imported sources, generated documents, release packages, and secrets are excluded.\n'
  printf 'Report path: %s\n' "${REPORT_PATH}"
} > "${REPORT_PATH}" 2>&1

printf 'Project Workbench audit selesai.\n'
printf 'Laporan: %s\n' "${REPORT_PATH}"
