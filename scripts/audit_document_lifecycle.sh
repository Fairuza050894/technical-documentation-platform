#!/usr/bin/env bash

set -u

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
REPORT_PATH="${HOME}/Downloads/technical-documentation-platform_document_lifecycle_${TIMESTAMP}.txt"

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
  printf '%s\n' 'DOCUMENT LIFECYCLE CORE AUDIT'
  printf '%s\n' '============================================================'
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "${PROJECT_ROOT}"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"

  run_section "Git status" git status --short --branch
  run_section "Whitespace" git diff --check
  run_section "Lifecycle module inventory" find \
    backend/src/tdp/modules/documents -type f -not -path '*/__pycache__/*' -print
  run_section "Ruff" uv run --project backend ruff check backend
  run_section "Ruff formatting" uv run --project backend ruff format --check backend
  run_section "Mypy" uv run --project backend mypy backend/src
  run_section "Backend tests" uv run --project backend pytest backend/tests
  run_section "ESLint" npm --prefix frontend run lint
  run_section "Vitest" npm --prefix frontend run test
  run_section "Production build" npm --prefix frontend run build
  run_section "Lifecycle API paths" uv run --project backend python -c \
    "from tdp.main import app; paths=app.openapi()['paths']; required={'/api/documents/{document_id}/versions','/api/document-versions/{version_id}','/api/document-versions/{version_id}/download','/api/document-versions/{version_id}/submit-review','/api/document-versions/{version_id}/request-changes','/api/document-versions/{version_id}/approve','/api/document-versions/{version_id}/supersede','/api/document-versions/{version_id}/workflow-events'}; assert required <= set(paths); print('Document lifecycle API paths verified')"

  printf '\nSafety: .env, SQLite data, generated Markdown content, runtime artifacts, and secrets are excluded.\n'
  printf 'Report path: %s\n' "${REPORT_PATH}"
} > "${REPORT_PATH}" 2>&1

printf 'Document Lifecycle audit selesai.\n'
printf 'Laporan: %s\n' "${REPORT_PATH}"
