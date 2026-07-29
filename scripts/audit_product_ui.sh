#!/usr/bin/env bash

set -u

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
REPORT_PATH="${HOME}/Downloads/technical-documentation-platform_product_ui_${TIMESTAMP}.txt"

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
  printf '%s\n' 'PRODUCT UI FOUNDATION AND OPERATIONAL OVERVIEW AUDIT'
  printf '%s\n' '============================================================'
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "${PROJECT_ROOT}"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"

  run_section "Git status" git status --short --branch
  run_section "Whitespace" git diff --check
  run_section "Product UI inventory" find \
    frontend/src/app frontend/src/modules/overview frontend/src/styles \
    -type f -not -path '*/__pycache__/*' -print
  run_section "Operational overview labels" grep -nE \
    'Operational workspace|Workspace metrics|Attention required|Recent activity|Project health|Quick actions' \
    frontend/src/modules/overview/OperationalOverview.tsx
  run_section "Grouped navigation labels" grep -nE \
    'Workspace|Sources|Documentation|System|System status' \
    frontend/src/app/App.tsx
  run_section "No foundation dashboard placeholder" bash -c \
    "! grep -q 'Foundation status' frontend/src/app/App.tsx"
  run_section "No unimplemented Sync History navigation" bash -c \
    "! grep -q 'Sync History' frontend/src/app/App.tsx"
  run_section "Accessibility capabilities" grep -nE \
    'focus-visible|prefers-reduced-motion|visually-hidden|caption' \
    frontend/src/styles/globals.css frontend/src/modules/overview/OperationalOverview.tsx
  run_section "Ruff" uv run --project backend ruff check backend
  run_section "Ruff formatting" uv run --project backend ruff format --check backend
  run_section "Mypy" uv run --project backend mypy backend/src
  run_section "Backend tests" uv run --project backend pytest backend/tests
  run_section "ESLint" npm --prefix frontend run lint
  run_section "Vitest" npm --prefix frontend run test
  run_section "Production build" npm --prefix frontend run build

  printf '\nSafety: .env, SQLite data, runtime artifacts, imported sources, generated documents, and secrets are excluded.\n'
  printf 'Report path: %s\n' "${REPORT_PATH}"
} > "${REPORT_PATH}" 2>&1

printf 'Product UI audit selesai.\n'
printf 'Laporan: %s\n' "${REPORT_PATH}"
