#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d ".git" || ! -f "Makefile" || ! -d "frontend/src" ]]; then
  printf 'ERROR: Run this script from the technical-documentation-platform repository root.\n' >&2
  exit 1
fi

TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
DOWNLOADS_DIR="${HOME}/Downloads"
REPORT="${DOWNLOADS_DIR}/technical-documentation-platform_visual_contract_cleanup_${TIMESTAMP}.txt"
TMP="$(mktemp)"
trap 'rm -f "${TMP}"' EXIT
mkdir -p "${DOWNLOADS_DIR}"

section() {
  printf '\n============================================================\n' >> "${TMP}"
  printf '%s\n' "$1" >> "${TMP}"
  printf '============================================================\n' >> "${TMP}"
}

run_block() {
  local title="$1"
  shift
  section "${title}"
  set +e
  "$@" >> "${TMP}" 2>&1
  local exit_code=$?
  set -e
  printf '[exit_code=%s]\n' "${exit_code}" >> "${TMP}"
  return "${exit_code}"
}

overall=0

{
  section "FRONTEND VISUAL CONTRACT CLEANUP AUDIT"
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "$(pwd)"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"
} >> "${TMP}"

run_block "Repository status before generation" git status --short --branch || overall=1

section "Shared warning notice contract"
for signal in \
  '.notice--warning {' \
  'border-left-color: var(--color-warning);' \
  'color: var(--color-warning);' \
  'background: var(--color-warning-subtle);'
do
  if grep -Fq "${signal}" frontend/src/styles/components.css; then
    printf 'PASS %s\n' "${signal}" >> "${TMP}"
  else
    printf 'FAIL %s\n' "${signal}" >> "${TMP}"
    overall=1
  fi
done

section "Empty modifier cleanup"
for selector in \
  'constraint-list--compact' \
  'document-section--generator' \
  'topbar--documents' \
  'topbar--operational'
do
  if grep -RIn --include='*.tsx' -- "${selector}" frontend/src >> "${TMP}" 2>&1; then
    printf 'FAIL empty modifier remains: %s\n' "${selector}" >> "${TMP}"
    overall=1
  else
    printf 'PASS removed empty modifier: %s\n' "${selector}" >> "${TMP}"
  fi
done

run_block "Generate repository documentation" make docs || overall=1
run_block "Targeted frontend architecture tests" \
  uv run --project backend pytest backend/tests/test_frontend_architecture.py -q || overall=1
run_block "Frontend lint" npm --prefix frontend run lint || overall=1
run_block "Frontend tests" npm --prefix frontend run test || overall=1
run_block "Frontend production build" npm --prefix frontend run build || overall=1
run_block "Full repository quality gate" make verify || overall=1
run_block "Whitespace" git diff --check || overall=1

section "Changed paths"
git status --short >> "${TMP}" 2>&1 || overall=1

section "Manual visual acceptance"
printf '%s\n' \
  "- Archived workspace, project, and feature notices use a restrained warning palette." \
  "- Warning notices remain distinct from error notices." \
  "- System Status documentation policy keeps its existing layout." \
  "- Overview and Documents topbars keep their existing visual behavior." \
  "- Document generator section keeps its existing layout and spacing." \
  "- No API, route, domain rule, database, or application behavior is changed." \
  >> "${TMP}"

section "Safety"
printf '%s\n' \
  "- The audit does not read .env values, credentials, tokens, SQLite records, or imported evidence." \
  "- No live or external endpoint is contacted." \
  "- The patch changes presentation contracts and architecture fitness tests only." \
  >> "${TMP}"

mv "${TMP}" "${REPORT}"
trap - EXIT

if [[ "${overall}" -eq 0 ]]; then
  printf 'Visual contract cleanup audit completed successfully.\n'
else
  printf 'Visual contract cleanup audit completed with findings.\n'
fi
printf 'Report: %s\n' "${REPORT}"
exit "${overall}"
