#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d ".git" || ! -f "Makefile" || ! -d "frontend/src" ]]; then
  printf 'ERROR: Run this script from the technical-documentation-platform repository root.\n' >&2
  exit 1
fi

TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
DOWNLOADS_DIR="${HOME}/Downloads"
REPORT="${DOWNLOADS_DIR}/technical-documentation-platform_changes_visual_fix_${TIMESTAMP}.txt"
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
  section "CHANGES WORKSPACE VISUAL REGRESSION FIX AUDIT"
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "$(pwd)"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"
} >> "${TMP}"

run_block "Repository status before generation" git status --short --branch || overall=1

section "Changes CSS contract"
for signal in \
  '.changes-results .status-grid' \
  '.changes-results .status-card' \
  '.changes-results .catalog-list' \
  '.changes-results .catalog-card__heading' \
  '.changes-results .method-badge' \
  '.changes-results .detail-list' \
  '.changes-results .detail-list code' \
  'overflow-wrap: anywhere;' \
  '@media (max-width: 760px)'
do
  if grep -Fq "${signal}" frontend/src/styles/modules/changes.css; then
    printf 'PASS %s\n' "${signal}" >> "${TMP}"
  else
    printf 'FAIL %s\n' "${signal}" >> "${TMP}"
    overall=1
  fi
done

if grep -Fq 'className="content-section changes-results"'   frontend/src/modules/changes/ChangesWorkspace.tsx; then
  printf 'PASS Changes result scope is present\n' >> "${TMP}"
else
  printf 'FAIL Changes result scope is missing\n' >> "${TMP}"
  overall=1
fi

run_block "Generate repository documentation" make docs || overall=1
run_block "Targeted frontend architecture tests"   uv run --project backend pytest backend/tests/test_frontend_architecture.py -q || overall=1
run_block "Changes component test"   npm --prefix frontend run test -- src/modules/changes/ChangesWorkspace.test.tsx || overall=1
run_block "Frontend lint" npm --prefix frontend run lint || overall=1
run_block "Frontend tests" npm --prefix frontend run test || overall=1
run_block "Frontend production build" npm --prefix frontend run build || overall=1
run_block "Full repository quality gate" make verify || overall=1
run_block "Whitespace" git diff --check || overall=1

section "Changed paths"
git status --short >> "${TMP}" 2>&1 || overall=1

section "Manual visual acceptance"
printf '%s\n' \
  "- Comparison summary is compact and contains no 190px empty cards." \
  "- Added, Modified, and Removed remain three aligned cells on desktop." \
  "- Every change is rendered as a separated structured record." \
  "- Entity type, entity key, severity, summary, change kind, and evidence pointers have clear hierarchy." \
  "- JSON Pointer values wrap without horizontal overflow." \
  "- At narrow widths, summary and detail metadata collapse to one column." \
  "- Comparison behavior and result data remain unchanged." \
  >> "${TMP}"

section "Safety"
printf '%s\n' \
  "- No API contract, database schema, domain rule, or comparison algorithm is changed." \
  "- The audit does not read .env values, credentials, tokens, SQLite data, or imported evidence." \
  "- No live or external endpoint is contacted." \
  >> "${TMP}"

mv "${TMP}" "${REPORT}"
trap - EXIT

if [[ "${overall}" -eq 0 ]]; then
  printf 'Changes visual fix audit completed successfully.\n'
else
  printf 'Changes visual fix audit completed with findings.\n'
fi
printf 'Report: %s\n' "${REPORT}"
exit "${overall}"
