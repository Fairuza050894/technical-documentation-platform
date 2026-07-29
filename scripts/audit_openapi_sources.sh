#!/usr/bin/env bash

set -u

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
REPORT_PATH="${HOME}/Downloads/technical-documentation-platform_sources_${TIMESTAMP}.txt"

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
  section "OPENAPI SOURCE MANAGEMENT AUDIT"
  printf 'Generated at               : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root               : %s\n' "${PROJECT_ROOT}"
  printf 'Current branch             : %s\n' "$(git branch --show-current 2>/dev/null || printf 'UNKNOWN')"
  printf 'Current commit             : %s\n' "$(git rev-parse HEAD 2>/dev/null || printf 'NO COMMIT')"
  printf 'Free disk                  : %s\n' "$(df -h . | awk 'NR==2 {print $4}')"

  section "REPOSITORY"
  run_check "Git status" git status --short --branch
  run_check "Whitespace validation" git diff --check
  run_check "Source module inventory" find backend/src/tdp/modules/sources -type f ! -path '*/__pycache__/*' | LC_ALL=C sort

  section "QUALITY GATES"
  run_check "Ruff" uv run --project backend ruff check backend
  run_check "Ruff formatting" uv run --project backend ruff format --check backend
  run_check "Mypy" uv run --project backend mypy backend/src
  run_check "Backend tests" uv run --project backend pytest backend/tests
  run_check "ESLint" npm --prefix frontend run lint
  run_check "Vitest" npm --prefix frontend run test
  run_check "Production build" npm --prefix frontend run build

  section "SOURCE API CONTRACT"
  run_check "OpenAPI source paths" uv run --project backend python -c \
    'from tdp.main import create_app; paths=create_app().openapi()["paths"]; expected={"/api/projects/{project_id}/sources/openapi", "/api/projects/{project_id}/sources", "/api/sources/{source_id}", "/api/sources/{source_id}/archive"}; missing=expected-set(paths); assert not missing, missing; print("Source API paths verified:", ", ".join(sorted(expected)))'

  run_check "OpenAPI fixture inspection" uv run --project backend python -c \
    'from pathlib import Path; from tdp.modules.sources.domain.model import SourceFileName; from tdp.modules.sources.infrastructure.openapi_inspector import DeterministicOpenApiInspector; path=Path("fixtures/openapi/commerce-api-v1.yaml"); result=DeterministicOpenApiInspector().inspect(SourceFileName(path.name), path.read_bytes()); assert result.operation_count == 3; print(result.api_title, result.openapi_version, result.operation_count)'

  section "LOCAL RUNTIME"
  if [ -d .runtime/artifacts ]; then
    printf 'Artifact directory          : PRESENT\n'
    printf 'Artifact disk usage         : %s\n' "$(du -sh .runtime/artifacts | awk '{print $1}')"
    printf 'Stored artifact files       : %s\n' "$(find .runtime/artifacts -type f | wc -l | tr -d ' ')"
  else
    printf 'Artifact directory          : NOT CREATED YET\n'
    printf 'Note                        : It will be created when the backend starts.\n'
  fi

  section "SAFETY"
  printf '%s\n' \
    '- Source file contents are not copied into this report.' \
    '- Artifact names, project records, and database contents are not listed.' \
    '- Secret values and .env contents are not collected.' \
    '- Imported files are stored locally and are never executed.'
} > "${REPORT_PATH}"

printf 'Audit OpenAPI Source selesai.\n'
printf 'Laporan lengkap: %s\n' "${REPORT_PATH}"
