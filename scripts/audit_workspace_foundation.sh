#!/usr/bin/env bash

set -u

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
REPORT_PATH="${HOME}/Downloads/technical-documentation-platform_workspace_foundation_${TIMESTAMP}.txt"

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
  printf '%s\n' 'WORKSPACE FOUNDATION AND CONTEXT SWITCHING AUDIT'
  printf '%s\n' '============================================================'
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "${PROJECT_ROOT}"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"

  run_section "Git status" git status --short --branch
  run_section "Whitespace" git diff --check
  run_section "Workspace module inventory" find \
    backend/src/tdp/modules/workspaces \
    frontend/src/modules/workspaces \
    -type f -not -path '*/__pycache__/*' -print
  run_section "Workspace API contract" grep -nE \
    'APIRouter\(prefix="/workspaces"|create_workspace|list_workspaces|get_workspace|archive_workspace' \
    backend/src/tdp/modules/workspaces/presentation/http/router.py
  run_section "Workspace-scoped project API" grep -nE \
    'workspace_projects_router|/workspaces/\{workspace_id\}/projects|list_by_workspace|ownership_type' \
    backend/src/tdp/modules/projects/presentation/http/router.py \
    backend/src/tdp/modules/projects/application/service.py \
    backend/src/tdp/modules/projects/infrastructure/sqlite_repository.py
  run_section "Additive project migration" grep -nE \
    'ALTER TABLE projects|DEFAULT_WORKSPACE_ID|ownership_type|workspace_id|ENTERPRISE.*TEAM' \
    backend/src/tdp/modules/projects/infrastructure/sqlite_repository.py \
    backend/tests/infrastructure/test_project_workspace_migration.py
  run_section "Workspace read-only governance" grep -nE \
    'WorkspaceArchivedError|WorkspaceStatus.ARCHIVED|DocumentProjectArchivedError|CatalogProjectArchivedError|is_active' \
    backend/src/tdp/modules/projects/application/service.py \
    backend/src/tdp/modules/sources/infrastructure/project_access.py \
    backend/src/tdp/modules/catalog/application/service.py \
    backend/src/tdp/modules/documents/application/service.py
  run_section "Canonical workspace routes" grep -nE \
    'workspaceHomePattern|workspaceProjectsPattern|workspaceProjectPattern|workspaceProjectStagePath|routeWorkspaceId' \
    frontend/src/app/router.ts
  run_section "Persistent Workspace selector" grep -nE \
    'LAST_WORKSPACE_KEY|WorkspaceSwitcher|WorkspaceRegistry|selectWorkspace|Manage workspaces' \
    frontend/src/app/App.tsx \
    frontend/src/modules/workspaces/WorkspaceSwitcher.tsx
  run_section "Professional Workspace switcher" grep -nE \
    'role="menu"|menuitemradio|Switch workspace|Find workspace|ArrowDown|Escape|mousedown|is-current' \
    frontend/src/modules/workspaces/WorkspaceSwitcher.tsx \
    frontend/src/modules/workspaces/WorkspaceSwitcher.test.tsx \
    frontend/src/styles/globals.css
  run_section "No native Workspace select" bash -c \
    "! grep -RInE '<select|workspace-selector' frontend/src/app frontend/src/modules/workspaces --include='*.tsx'"
  run_section "Workspace-scoped frontend data" grep -nE \
    'listProjects\(workspace.id|workspace=\{activeWorkspace\}|workspaceId=\{route.workspaceId\}|Only projects assigned' \
    frontend/src/app/App.tsx \
    frontend/src/modules/overview/OperationalOverview.tsx \
    frontend/src/modules/projects/ProjectWorkspace.tsx
  run_section "No Workspace type UI" bash -c \
    "! grep -RInE 'Workspace type|formatWorkspace|id=\"workspace-type\"' frontend/src --include='*.tsx' --include='*.ts'"
  run_section "Document control terminology" grep -nE \
    'Workspace ID|Ownership|Workspace type' \
    backend/src/tdp/modules/documents/infrastructure/markdown_renderer.py \
    backend/tests/infrastructure/test_markdown_renderer.py
  run_section "Workspace and routing tests" grep -RInE \
    'default workspace|workspace-scoped|legacy project deep link|switches workspace|another workspace|protects the default workspace|read-only' \
    backend/tests \
    frontend/src/app \
    frontend/src/modules/workspaces \
    frontend/src/modules/projects \
    frontend/src/modules/workbench \
    --include='*.py' --include='*.test.ts' --include='*.test.tsx'
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

printf 'Workspace Foundation audit selesai.\n'
printf 'Laporan: %s\n' "${REPORT_PATH}"
