#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d ".git" || ! -f "Makefile" || ! -d "frontend/src" ]]; then
  printf 'ERROR: Run this script from the technical-documentation-platform repository root.\n' >&2
  exit 1
fi

TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
DOWNLOADS_DIR="${HOME}/Downloads"
REPORT="${DOWNLOADS_DIR}/technical-documentation-platform_system_status_visual_fix_${TIMESTAMP}.txt"
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
  section "SYSTEM STATUS VISUAL REGRESSION FIX AUDIT"
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "$(pwd)"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"
} >> "${TMP}"

run_block "Repository status before generation" git status --short --branch || overall=1

section "System Status CSS contract"
for signal in \
  'display: grid;' \
  'grid-template-columns: minmax(220px, 1.8fr) repeat(3, minmax(120px, 1fr));' \
  'gap: 1px;' \
  '.system-status-grid > div' \
  '.system-status-grid dt' \
  '.system-status-grid dd'
do
  if grep -Fq "${signal}" frontend/src/styles/components.css; then
    printf 'PASS %s\n' "${signal}" >> "${TMP}"
  else
    printf 'FAIL %s\n' "${signal}" >> "${TMP}"
    overall=1
  fi
done

run_block "Generate repository documentation" make docs || overall=1
run_block "Targeted frontend architecture test" \
  uv run --project backend pytest \
  backend/tests/test_frontend_architecture.py \
  -q || overall=1
run_block "Frontend lint" npm --prefix frontend run lint || overall=1
run_block "Frontend tests" npm --prefix frontend run test || overall=1
run_block "Frontend production build" npm --prefix frontend run build || overall=1
run_block "Full repository quality gate" make verify || overall=1
run_block "Whitespace" git diff --check || overall=1

section "Changed paths"
git status --short >> "${TMP}" 2>&1 || overall=1

section "Manual visual acceptance"
printf '%s\n' \
  "- Desktop: Runtime status renders as four aligned metadata cells." \
  "- Service receives the wider first column; Availability, Version, and Environment remain readable." \
  "- Labels use an uppercase metadata hierarchy and values do not overlap." \
  "- Narrow viewport: the existing responsive rule collapses the grid to one column." \
  "- Documentation policy, sidebar, breadcrumb, and runtime badges remain unchanged." \
  >> "${TMP}"

section "Safety"
printf '%s\n' \
  "- No API contract, database schema, domain rule, or runtime data is changed." \
  "- The audit does not read .env values, credentials, tokens, SQLite data, or imported evidence." \
  "- No live or external endpoint is contacted." \
  >> "${TMP}"

mv "${TMP}" "${REPORT}"
trap - EXIT

if [[ "${overall}" -eq 0 ]]; then
  printf 'System Status visual fix audit completed successfully.\n'
else
  printf 'System Status visual fix audit completed with findings.\n'
fi
printf 'Report: %s\n' "${REPORT}"
exit "${overall}"
