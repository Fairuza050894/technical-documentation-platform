#!/usr/bin/env bash

set -u

PROJECT_ROOT="${1:-$(pwd)}"
TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
DOWNLOADS_DIR="${HOME}/Downloads"
REPORT_PATH="${DOWNLOADS_DIR}/technical-documentation-platform_mvp1_next_context_${TIMESTAMP}.txt"

mkdir -p "${DOWNLOADS_DIR}"

section() {
  printf '\n============================================================\n'
  printf '%s\n' "$1"
  printf '============================================================\n'
}

file_digest() {
  local file_path="$1"

  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "${file_path}" | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "${file_path}" | awk '{print $1}'
  else
    printf 'UNAVAILABLE'
  fi
}

emit_file() {
  local relative_path="$1"
  local absolute_path="${PROJECT_ROOT}/${relative_path}"

  if [ ! -f "${absolute_path}" ]; then
    printf '\n[MISSING FILE] %s\n' "${relative_path}"
    return
  fi

  printf '\n----- BEGIN FILE: %s -----\n' "${relative_path}"
  printf 'SHA256: %s\n' "$(file_digest "${absolute_path}")"
  printf '%s\n' '----- CONTENT -----'
  cat "${absolute_path}"
  printf '\n----- END FILE: %s -----\n' "${relative_path}"
}

if [ ! -d "${PROJECT_ROOT}/.git" ]; then
  printf 'Error: %s bukan root repository Git.\n' "${PROJECT_ROOT}" >&2
  exit 1
fi

FILES=(
  "Makefile"
  "README.md"
  "backend/pyproject.toml"
  "backend/src/tdp/config.py"
  "backend/src/tdp/main.py"
  "backend/src/tdp/presentation/http/errors.py"
  "backend/src/tdp/presentation/http/routers/health.py"
  "backend/src/tdp/modules/projects/application/service.py"
  "backend/src/tdp/modules/projects/domain/model.py"
  "backend/src/tdp/modules/projects/domain/repository.py"
  "backend/src/tdp/modules/projects/infrastructure/sqlite_repository.py"
  "backend/src/tdp/modules/projects/presentation/http/router.py"
  "backend/src/tdp/modules/sources/application/commands.py"
  "backend/src/tdp/modules/sources/application/dto.py"
  "backend/src/tdp/modules/sources/application/ports.py"
  "backend/src/tdp/modules/sources/application/service.py"
  "backend/src/tdp/modules/sources/domain/errors.py"
  "backend/src/tdp/modules/sources/domain/model.py"
  "backend/src/tdp/modules/sources/domain/repository.py"
  "backend/src/tdp/modules/sources/infrastructure/local_artifact_store.py"
  "backend/src/tdp/modules/sources/infrastructure/openapi_inspector.py"
  "backend/src/tdp/modules/sources/infrastructure/project_access.py"
  "backend/src/tdp/modules/sources/infrastructure/sqlite_repository.py"
  "backend/src/tdp/modules/sources/presentation/http/router.py"
  "backend/tests/test_architecture.py"
  "backend/tests/presentation/test_sources_api.py"
  "frontend/package.json"
  "frontend/eslint.config.js"
  "frontend/src/app/App.tsx"
  "frontend/src/app/App.test.tsx"
  "frontend/src/shared/api/client.ts"
  "frontend/src/modules/projects/api.ts"
  "frontend/src/modules/projects/types.ts"
  "frontend/src/modules/sources/api.ts"
  "frontend/src/modules/sources/types.ts"
  "frontend/src/modules/sources/SourceWorkspace.tsx"
  "frontend/src/modules/sources/SourceWorkspace.test.tsx"
  "frontend/src/styles/tokens.css"
  "frontend/src/styles/globals.css"
  "frontend/src/test/setup.ts"
)

{
  section "MVP 1 NEXT-PATCH CONTEXT"
  printf 'Generated at               : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root               : %s\n' "${PROJECT_ROOT}"
  printf 'Current branch             : %s\n' "$(git -C "${PROJECT_ROOT}" branch --show-current 2>/dev/null || printf 'UNKNOWN')"
  printf 'Current commit             : %s\n' "$(git -C "${PROJECT_ROOT}" rev-parse HEAD 2>/dev/null || printf 'NO COMMIT')"
  printf 'Free disk                  : %s\n' "$(df -h "${PROJECT_ROOT}" | awk 'NR==2 {print $4}')"

  section "REPOSITORY STATE"
  git -C "${PROJECT_ROOT}" status --short --branch 2>&1
  printf '\n--- Recent commits ---\n'
  git -C "${PROJECT_ROOT}" log --oneline -5 2>&1 || true
  printf '\n--- Diff summary ---\n'
  git -C "${PROJECT_ROOT}" diff --stat 2>&1 || true
  printf '\n--- Staged diff summary ---\n'
  git -C "${PROJECT_ROOT}" diff --cached --stat 2>&1 || true
  printf '\n--- Whitespace validation ---\n'
  git -C "${PROJECT_ROOT}" diff --check 2>&1 || true
  git -C "${PROJECT_ROOT}" diff --cached --check 2>&1 || true

  section "RELEVANT FILE INVENTORY"
  printf 'Selected files only; runtime data, .env, credentials, and imported artifacts are excluded.\n'
  for relative_path in "${FILES[@]}"; do
    if [ -f "${PROJECT_ROOT}/${relative_path}" ]; then
      printf 'FOUND   %s\n' "${relative_path}"
    else
      printf 'MISSING %s\n' "${relative_path}"
    fi
  done

  section "SELECTED FILE CONTENTS"
  for relative_path in "${FILES[@]}"; do
    emit_file "${relative_path}"
  done

  section "SAFETY"
  printf '%s\n' \
    '- .env files and environment variable values are not collected.' \
    '- SQLite database contents are not collected.' \
    '- Imported OpenAPI artifact contents under .runtime are not collected.' \
    '- Git credentials, tokens, and npm credentials are not collected.' \
    '- This report contains source code from this dashboard repository only.' \
    '- Review the report before uploading if the repository contains custom sensitive code.'

  section "EXPORT COMPLETED"
  printf 'Report path                : %s\n' "${REPORT_PATH}"
} > "${REPORT_PATH}"

printf 'Export konteks MVP 1 selesai.\n'
printf 'Laporan lengkap: %s\n' "${REPORT_PATH}"
