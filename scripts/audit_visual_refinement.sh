#!/usr/bin/env bash

set -u

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
REPORT_PATH="${HOME}/Downloads/technical-documentation-platform_visual_refinement_${TIMESTAMP}.txt"

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
  printf '%s\n' 'VISUAL REFINEMENT AND PRODUCT POLISH AUDIT'
  printf '%s\n' '============================================================'
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "${PROJECT_ROOT}"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"

  run_section "Git status" git status --short --branch
  run_section "Whitespace" git diff --check
  run_section "Visual refinement inventory" find \
    frontend/src/app frontend/src/modules/overview frontend/src/shared/ui frontend/src/styles \
    -type f -not -path '*/__pycache__/*' -print
  run_section "Sidebar icon mapping" grep -nE \
    'icon: "(overview|projects|source|catalog|changes|documents|server)"|navigation-item__icon' \
    frontend/src/app/App.tsx
  run_section "Operational workbench composition" grep -nE \
    'signal-strip|operations-workbench|activity-stream|operations-rail|Attention required|Quick actions|Project health' \
    frontend/src/modules/overview/OperationalOverview.tsx
  run_section "No generic metric-card overview" bash -c \
    "! grep -q 'metric-card' frontend/src/modules/overview/OperationalOverview.tsx"
  run_section "Refined control and table styles" grep -nE \
    'appearance: none|--control-height|workspace-filter|table-frame--dense|numeric-cell|document-section|document-generation-form' \
    frontend/src/styles/globals.css frontend/src/styles/tokens.css \
    frontend/src/modules/documents/DocumentsWorkspace.tsx
  run_section "Typography and layout tokens" grep -nE \
    -- '--font-sans|--font-mono|--sidebar-width|--utility-height|letter-spacing|font-variant-numeric' \
    frontend/src/styles/tokens.css frontend/src/styles/globals.css
  run_section "R1 async test resilience" grep -nE \
    'configure\(\{ asyncUtilTimeout: 5000 \}\)' \
    frontend/src/test/setup.ts
  run_section "R1 operational hierarchy" grep -nE \
    'operations-rail|rail-section:first-child|signal-item__icon|document-section--generator|document-generation-status' \
    frontend/src/styles/globals.css \
    frontend/src/modules/documents/DocumentsWorkspace.tsx
  run_section "R1 color normalization" grep -nE \
    -- '--color-background: #f5f7fa|--color-sidebar: #0f1924|--color-success: #23855d|--color-danger: #b93838' \
    frontend/src/styles/tokens.css
  run_section "R2 navigation and lifecycle language" grep -nE \
    'documentElement.scrollTop|Replaced by v|Mark as replaced|formatCount\(versions.length|latestSourceId|source-reference' \
    frontend/src/app/App.tsx \
    frontend/src/modules/documents/DocumentsWorkspace.tsx \
    frontend/src/modules/catalog/ApiCatalogWorkspace.tsx
  run_section "R2 no user-facing Superseded text" bash -c \
    "! grep -RIn --include='*.tsx' --include='*.ts' 'Superseded' frontend/src/app frontend/src/modules"
  run_section "R2 final control polish" grep -nE \
    'Patch 0009.6-R2|button--primary:disabled|document-revision-reason|scroll-padding-top|status-badge--superseded' \
    frontend/src/styles/globals.css
  run_section "Accessibility capabilities" grep -nE \
    'focus-visible|prefers-reduced-motion|visually-hidden|aria-label|caption' \
    frontend/src/styles/globals.css \
    frontend/src/app/App.tsx \
    frontend/src/modules/overview/OperationalOverview.tsx
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

printf 'Visual refinement audit selesai.\n'
printf 'Laporan: %s\n' "${REPORT_PATH}"
