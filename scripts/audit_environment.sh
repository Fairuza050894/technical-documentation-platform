#!/usr/bin/env bash

set -u

PROJECT_NAME="technical-documentation-platform"
TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
DOWNLOADS_DIR="${HOME}/Downloads"
REPORT_PATH="${DOWNLOADS_DIR}/${PROJECT_NAME}_audit_${TIMESTAMP}.txt"

mkdir -p "${DOWNLOADS_DIR}"

section() {
  printf '\n============================================================\n'
  printf '%s\n' "$1"
  printf '============================================================\n'
}

print_command_version() {
  local label="$1"
  local command_name="$2"
  shift 2

  if command -v "${command_name}" >/dev/null 2>&1; then
    printf '%-24s : ' "${label}"
    "$@" 2>&1 | head -n 1
  else
    printf '%-24s : NOT INSTALLED\n' "${label}"
  fi
}

safe_run() {
  local label="$1"
  shift

  printf '\n--- %s ---\n' "${label}"
  "$@" 2>&1 || printf '[command failed with exit code %s]\n' "$?"
}

repo_root=""
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"
fi

{
  section "AUDIT METADATA"
  printf 'Project                    : %s\n' "${PROJECT_NAME}"
  printf 'Generated at               : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Current directory          : %s\n' "$(pwd)"
  printf 'User                       : %s\n' "$(id -un 2>/dev/null || printf 'unknown')"
  printf 'Shell                      : %s\n' "${SHELL:-unknown}"

  section "OPERATING SYSTEM"
  if command -v sw_vers >/dev/null 2>&1; then
    safe_run "macOS version" sw_vers
  fi
  safe_run "Kernel and architecture" uname -a
  safe_run "CPU architecture" uname -m
  safe_run "Disk usage" df -h .

  section "DEVELOPER TOOLCHAIN"
  print_command_version "Git" git git --version
  print_command_version "GitHub CLI" gh gh --version
  print_command_version "Node.js" node node --version
  print_command_version "npm" npm npm --version
  print_command_version "pnpm" pnpm pnpm --version
  print_command_version "Yarn" yarn yarn --version
  print_command_version "Python 3" python3 python3 --version
  print_command_version "pip 3" pip3 pip3 --version
  print_command_version "uv" uv uv --version
  print_command_version "Poetry" poetry poetry --version
  print_command_version "Docker" docker docker --version
  print_command_version "Docker Compose" docker docker compose version
  print_command_version "PostgreSQL client" psql psql --version
  print_command_version "Redis client" redis-cli redis-cli --version
  print_command_version "Make" make make --version
  print_command_version "OpenSSL" openssl openssl version
  print_command_version "curl" curl curl --version

  if command -v xcode-select >/dev/null 2>&1; then
    safe_run "Xcode Command Line Tools" xcode-select -p
  fi

  section "RUNTIME PATHS"
  for command_name in git gh node npm pnpm yarn python3 pip3 uv poetry docker psql redis-cli make; do
    if command -v "${command_name}" >/dev/null 2>&1; then
      printf '%-24s : %s\n' "${command_name}" "$(command -v "${command_name}")"
    else
      printf '%-24s : NOT FOUND\n' "${command_name}"
    fi
  done

  section "GIT CONFIGURATION"
  if command -v git >/dev/null 2>&1; then
    printf 'User name                  : %s\n' "$(git config --global user.name 2>/dev/null || printf 'NOT SET')"
    printf 'User email                 : %s\n' "$(git config --global user.email 2>/dev/null || printf 'NOT SET')"
    printf 'Default branch             : %s\n' "$(git config --global init.defaultBranch 2>/dev/null || printf 'NOT SET')"
    printf 'Credential helper          : %s\n' "$(git config --global credential.helper 2>/dev/null || printf 'NOT SET')"
  else
    printf 'Git is not installed.\n'
  fi

  section "REPOSITORY STATE"
  if [ -n "${repo_root}" ]; then
    printf 'Repository root            : %s\n' "${repo_root}"
    printf 'Current branch             : %s\n' "$(git branch --show-current 2>/dev/null || printf 'DETACHED/UNKNOWN')"
    printf 'Current commit             : %s\n' "$(git rev-parse HEAD 2>/dev/null || printf 'NO COMMIT')"
    printf 'Remote origin              : %s\n' "$(git remote get-url origin 2>/dev/null || printf 'NOT SET')"
    safe_run "Git status" git status --short --branch
    safe_run "Tracked top-level files" git ls-files | sed -n '1,200p'
  else
    printf 'Current directory is not inside a Git repository.\n'
  fi

  section "PROJECT FILE INVENTORY"
  printf 'Only file names are collected. File contents and secrets are not read.\n'
  if command -v find >/dev/null 2>&1; then
    find . \
      -maxdepth 3 \
      -type f \
      ! -path './.git/*' \
      ! -path './node_modules/*' \
      ! -path './.venv/*' \
      ! -path './venv/*' \
      ! -path './dist/*' \
      ! -path './build/*' \
      ! -name '.env' \
      ! -name '.env.*' \
      | LC_ALL=C sort \
      | sed -n '1,400p'
  fi

  section "PROJECT CONFIGURATION FILES"
  for candidate in \
    pyproject.toml \
    requirements.txt \
    package.json \
    package-lock.json \
    pnpm-lock.yaml \
    yarn.lock \
    docker-compose.yml \
    compose.yml \
    Makefile \
    .python-version \
    .nvmrc; do
    if [ -f "${candidate}" ]; then
      printf 'FOUND                      : %s\n' "${candidate}"
    else
      printf 'MISSING                    : %s\n' "${candidate}"
    fi
  done

  section "LOCAL SERVICE STATUS"
  if command -v docker >/dev/null 2>&1; then
    safe_run "Docker daemon" docker info --format 'Server version: {{.ServerVersion}}'
    safe_run "Docker containers" docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
  else
    printf 'Docker is not installed.\n'
  fi

  section "NETWORK PORT AVAILABILITY"
  printf 'The audit checks local listening ports only; no external network request is made.\n'
  if command -v lsof >/dev/null 2>&1; then
    for port in 3000 5173 8000 5432 6379 9000 9001; do
      if lsof -nP -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1; then
        printf 'Port %-5s                : IN USE\n' "${port}"
      else
        printf 'Port %-5s                : AVAILABLE\n' "${port}"
      fi
    done
  else
    printf 'lsof is unavailable; port checks were skipped.\n'
  fi

  section "SECURITY SAFETY NOTES"
  printf '%s\n' \
    '- Environment variable values were not collected.' \
    '- .env file contents were not collected.' \
    '- Git credentials and access tokens were not collected.' \
    '- Source file contents were not collected.' \
    '- The report may contain local paths, Git remote URLs, and Git identity metadata.' \
    '- Review the report before uploading if any of those are considered sensitive.'

  section "AUDIT COMPLETED"
  printf 'Report path                : %s\n' "${REPORT_PATH}"
} > "${REPORT_PATH}"

tool_count=0
missing_count=0
for command_name in git node npm python3 docker; do
  if command -v "${command_name}" >/dev/null 2>&1; then
    tool_count=$((tool_count + 1))
  else
    missing_count=$((missing_count + 1))
  fi
done

printf 'Audit selesai: %s tool inti ditemukan, %s belum tersedia.\n' "${tool_count}" "${missing_count}"
printf 'Laporan lengkap: %s\n' "${REPORT_PATH}"
