#!/usr/bin/env bash

set -u

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
REPORT_PATH="${HOME}/Downloads/technical-documentation-platform_projects_${TIMESTAMP}.txt"

mkdir -p "${HOME}/Downloads"
cd "${PROJECT_ROOT}"

section() {
  printf '\n============================================================\n'
  printf '%s\n' "$1"
  printf '============================================================\n'
}

run_check() {
  local label="$1"
  shift
  local exit_code=0

  printf '\n--- %s ---\n' "${label}"
  "$@" 2>&1 || exit_code=$?
  printf '[exit_code=%s]\n' "${exit_code}"
}

{
  section "PROJECT MANAGEMENT AUDIT"
  printf 'Generated at               : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root               : %s\n' "${PROJECT_ROOT}"
  printf 'Current branch             : %s\n' "$(git branch --show-current 2>/dev/null || printf 'UNKNOWN')"
  printf 'Current commit             : %s\n' "$(git rev-parse HEAD 2>/dev/null || printf 'NO COMMIT')"
  printf 'Free disk                  : %s\n' "$(df -h . | awk 'NR==2 {print $4}')"

  section "REPOSITORY"
  run_check "Git status" git status --short --branch
  run_check "Whitespace validation" git diff --check
  run_check "Project module inventory" find backend/src/tdp/modules/projects -type f ! -path '*/__pycache__/*' | LC_ALL=C sort

  section "BACKEND QUALITY"
  run_check "Ruff" uv run --project backend ruff check backend
  run_check "Ruff formatting" uv run --project backend ruff format --check backend
  run_check "Mypy" uv run --project backend mypy backend/src
  run_check "Project tests" uv run --project backend pytest backend/tests

  section "FRONTEND QUALITY"
  run_check "ESLint" npm --prefix frontend run lint
  run_check "Vitest" npm --prefix frontend run test
  run_check "Production build" npm --prefix frontend run build

  section "PROJECT API CONTRACT"
  run_check "OpenAPI project paths" uv run --project backend python -c \
    'from tdp.main import create_app; paths=create_app().openapi()["paths"]; expected={"/api/projects", "/api/projects/{project_id}", "/api/projects/{project_id}/archive"}; missing=expected-set(paths); assert not missing, missing; print("Project API paths verified:", ", ".join(sorted(expected)))'

  section "LOCAL RUNTIME"
  if [ -f .runtime/tdp.sqlite3 ]; then
    printf 'Local database             : PRESENT\n'
    printf 'Database size              : %s\n' "$(du -h .runtime/tdp.sqlite3 | awk '{print $1}')"
  else
    printf 'Local database             : NOT CREATED YET\n'
    printf 'Note                       : It will be created when the backend starts.\n'
  fi

  section "SAFETY"
  printf '%s\n' \
    '- The report does not include project records or database contents.' \
    '- Secret values and .env contents are not collected.' \
    '- The SQLite file itself is not copied into the report.'
} > "${REPORT_PATH}"

printf 'Audit Project Management selesai.\n'
printf 'Laporan lengkap: %s\n' "${REPORT_PATH}"
