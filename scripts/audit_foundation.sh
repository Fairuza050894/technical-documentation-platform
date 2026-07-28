#!/usr/bin/env bash

set -u

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
REPORT_PATH="${HOME}/Downloads/technical-documentation-platform_foundation_${TIMESTAMP}.txt"

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
  section "FOUNDATION AUDIT"
  printf 'Generated at               : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root               : %s\n' "${PROJECT_ROOT}"
  printf 'Current branch             : %s\n' "$(git branch --show-current 2>/dev/null || printf 'UNKNOWN')"
  printf 'Current commit             : %s\n' "$(git rev-parse HEAD 2>/dev/null || printf 'NO COMMIT')"
  printf 'Free disk                  : %s\n' "$(df -h . | awk 'NR==2 {print $4}')"

  section "TOOLCHAIN"
  for command_name in git node npm python3 uv brew; do
    if command -v "${command_name}" >/dev/null 2>&1; then
      printf '%-24s : %s\n' "${command_name}" "$(command -v "${command_name}")"
    else
      printf '%-24s : NOT FOUND\n' "${command_name}"
    fi
  done
  node --version 2>/dev/null || true
  python3 --version 2>/dev/null || true
  uv --version 2>/dev/null || true

  section "REPOSITORY"
  run_check "Git status" git status --short --branch
  run_check "Whitespace validation" git diff --check
  run_check "File inventory" find . -maxdepth 4 -type f ! -path './.git/*' ! -path './frontend/node_modules/*' ! -path './backend/.venv/*' | LC_ALL=C sort

  section "BACKEND"
  if command -v uv >/dev/null 2>&1 && [ -f backend/uv.lock ]; then
    run_check "Ruff" uv run --project backend ruff check backend
    run_check "Ruff formatting" uv run --project backend ruff format --check backend
    run_check "Mypy" uv run --project backend mypy backend/src
    run_check "Pytest" uv run --project backend pytest backend/tests
  else
    printf 'Backend dependencies are not installed. Run: make bootstrap\n'
  fi

  section "FRONTEND"
  if [ -d frontend/node_modules ]; then
    run_check "ESLint" npm --prefix frontend run lint
    run_check "Vitest" npm --prefix frontend run test
    run_check "Production build" npm --prefix frontend run build
  else
    printf 'Frontend dependencies are not installed. Run: make bootstrap\n'
  fi

  section "NETWORK PORTS"
  for port in 4173 8000; do
    if lsof -nP -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1; then
      printf 'Port %-5s                : IN USE\n' "${port}"
    else
      printf 'Port %-5s                : AVAILABLE\n' "${port}"
    fi
  done

  section "SAFETY"
  printf '%s\n' \
    '- Secret values and .env contents are not collected.' \
    '- Source file contents are not included.' \
    '- The report may include local paths and tool versions.'
} > "${REPORT_PATH}"

printf 'Audit foundation selesai.\n'
printf 'Laporan lengkap: %s\n' "${REPORT_PATH}"
