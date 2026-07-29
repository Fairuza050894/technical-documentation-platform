#!/usr/bin/env bash

set -u

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_PATH="${HOME}/Downloads/technical-documentation-platform_changes_$(date '+%Y%m%d_%H%M%S').txt"

run_check() {
  local title="$1"
  shift
  printf '\n--- %s ---\n' "${title}"
  "$@"
  printf '[exit_code=%s]\n' "$?"
}

{
  printf '============================================================\n'
  printf 'CHANGE DETECTION AUDIT\n'
  printf '============================================================\n'
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "${PROJECT_ROOT}"
  printf 'Branch       : %s\n' "$(git -C "${PROJECT_ROOT}" branch --show-current)"
  printf 'Commit       : %s\n' "$(git -C "${PROJECT_ROOT}" rev-parse HEAD)"

  run_check "Git status" git -C "${PROJECT_ROOT}" status --short --branch
  run_check "Whitespace" git -C "${PROJECT_ROOT}" diff --check
  run_check "Ruff" uv run --project "${PROJECT_ROOT}/backend" ruff check "${PROJECT_ROOT}/backend"
  run_check "Ruff formatting" uv run --project "${PROJECT_ROOT}/backend" ruff format --check "${PROJECT_ROOT}/backend"
  run_check "Mypy" uv run --project "${PROJECT_ROOT}/backend" mypy "${PROJECT_ROOT}/backend/src"
  run_check "Backend tests" uv run --project "${PROJECT_ROOT}/backend" pytest "${PROJECT_ROOT}/backend/tests"
  run_check "ESLint" npm --prefix "${PROJECT_ROOT}/frontend" run lint
  run_check "Vitest" npm --prefix "${PROJECT_ROOT}/frontend" run test
  run_check "Production build" npm --prefix "${PROJECT_ROOT}/frontend" run build

  printf '\nSafety: .env, SQLite data, runtime artifacts, and secrets are excluded.\n'
  printf 'Report path: %s\n' "${REPORT_PATH}"
} > "${REPORT_PATH}" 2>&1

printf 'Change Detection audit selesai.\n'
printf 'Laporan: %s\n' "${REPORT_PATH}"
