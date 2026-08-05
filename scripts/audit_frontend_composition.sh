#!/usr/bin/env bash
set -u

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
REPORT_PATH="${HOME}/Downloads/technical-documentation-platform_frontend_composition_${TIMESTAMP}.txt"

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
  printf '%s\n' 'FRONTEND COMPOSITION AND CSS FOUNDATION AUDIT'
  printf '%s\n' '============================================================'
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "${PROJECT_ROOT}"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"

  run_section "Git status" git status --short --branch
  run_section "Whitespace" git diff --check
  run_section "Documentation freshness" python3 scripts/generate_repository_docs.py --check
  run_section "App composition inventory" find \
    frontend/src/app -type f \( -name '*.ts' -o -name '*.tsx' \) -print | sort
  run_section "App line bound" bash -lc '
    lines="$(wc -l < frontend/src/app/App.tsx | tr -d " ")"
    printf "App.tsx lines: %s\n" "$lines"
    [[ "$lines" -le 340 ]]
  '
  run_section "Application shell boundaries" grep -nE \
    'AppShell|RouteContent|buildNavigationGroups|resolvePageContext|useHealthStatus' \
    frontend/src/app/App.tsx
  run_section "No shell markup in App" bash -lc \
    '! grep -qE "<aside|<main|function SystemStatus|function RouteNotFound" frontend/src/app/App.tsx'
  run_section "CSS import manifest" cat frontend/src/styles/globals.css
  run_section "CSS layer sizes" bash -lc \
    'wc -l frontend/src/styles/*.css frontend/src/styles/modules/*.css | sort -nr'
  run_section "No CSS patch-history comments" bash -lc \
    '! grep -R -nE "Patch 0009|patch 0009" frontend/src/styles --include="*.css"'
  run_section "Frontend architecture tests" uv run --project backend pytest \
    backend/tests/test_frontend_architecture.py
  run_section "Frontend lint" npm --prefix frontend run lint
  run_section "Frontend tests" npm --prefix frontend run test
  run_section "Frontend production build" npm --prefix frontend run build
  run_section "Full repository quality gate" make verify

  printf '\nSafety: .env values, SQLite data, runtime artifacts, imported sources, generated customer documents, credentials, and secrets are excluded.\n'
} > "${REPORT_PATH}" 2>&1

printf 'Frontend Composition audit completed.\n'
printf 'Report: %s\n' "${REPORT_PATH}"
