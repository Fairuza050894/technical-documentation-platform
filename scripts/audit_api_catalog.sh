#!/usr/bin/env bash

set -u

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
REPORT_PATH="${HOME}/Downloads/technical-documentation-platform_catalog_${TIMESTAMP}.txt"

section() {
  printf '\n============================================================\n'
  printf '%s\n' "$1"
  printf '============================================================\n'
}

run_check() {
  local label="$1"
  shift
  printf '\n--- %s ---\n' "${label}"
  (
    cd "${PROJECT_ROOT}" || exit 1
    "$@"
  )
  printf '[exit_code=%s]\n' "$?"
}

mkdir -p "${HOME}/Downloads"

{
  section "API CATALOG AUDIT"
  printf 'Generated at               : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root               : %s\n' "${PROJECT_ROOT}"
  printf 'Current branch             : %s\n' "$(git -C "${PROJECT_ROOT}" branch --show-current)"
  printf 'Current commit             : %s\n' "$(git -C "${PROJECT_ROOT}" rev-parse HEAD)"

  section "REPOSITORY"
  run_check "Git status" git status --short --branch
  run_check "Whitespace validation" git diff --check
  run_check "Catalog module inventory" find backend/src/tdp/modules/catalog -type f -name '*.py' -print

  section "QUALITY GATES"
  run_check "Ruff" uv run --project backend ruff check backend
  run_check "Ruff formatting" uv run --project backend ruff format --check backend
  run_check "Mypy" uv run --project backend mypy backend/src
  run_check "Backend tests" uv run --project backend pytest backend/tests
  run_check "ESLint" npm --prefix frontend run lint
  run_check "Vitest" npm --prefix frontend run test
  run_check "Production build" npm --prefix frontend run build

  section "API CONTRACT"
  run_check "Catalog API paths" uv run --project backend python -c     "from tdp.main import app; paths=app.openapi()['paths']; required={'/api/sources/{source_id}/synchronizations','/api/synchronizations/{run_id}','/api/projects/{project_id}/api-catalog'}; missing=required-set(paths); assert not missing, missing; print('Catalog API paths verified')"

  section "SAFETY"
  printf '%s\n'     '- Imported source contents are not included.'     '- SQLite records and artifact contents are not included.'     '- Secrets and .env values are not collected.'     '- Synchronization counts are verified through automated tests.'

  section "AUDIT COMPLETED"
  printf 'Report path                : %s\n' "${REPORT_PATH}"
} > "${REPORT_PATH}" 2>&1

printf 'Audit API Catalog selesai.\n'
printf 'Laporan lengkap: %s\n' "${REPORT_PATH}"
