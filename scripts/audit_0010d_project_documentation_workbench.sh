#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d ".git" || ! -f "Makefile" || ! -f "frontend/src/modules/workbench/ProjectDocumentationOverview.tsx" ]]; then
  printf 'ERROR: Run this script from the technical-documentation-platform repository root.\n' >&2
  exit 1
fi

TS="$(date '+%Y%m%d_%H%M%S')"
REPORT="${HOME}/Downloads/technical-documentation-platform_0010d_project_documentation_workbench_${TS}.txt"
TMP="$(mktemp)"
trap 'rm -f "${TMP}"' EXIT
mkdir -p "${HOME}/Downloads"

section() {
  printf '\n============================================================\n%s\n============================================================\n' "$1" >> "${TMP}"
}

run_block() {
  local title="$1"
  shift
  section "${title}"
  set +e
  "$@" >> "${TMP}" 2>&1
  local rc=$?
  set -e
  printf '[exit_code=%s]\n' "${rc}" >> "${TMP}"
  return "${rc}"
}

overall=0

{
  section "0010D PROJECT DOCUMENTATION WORKBENCH AUDIT"
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "$(pwd)"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"
} >> "${TMP}"

run_block "Repository status before generation" git status --short --branch || overall=1

run_block "Focused workbench frontend tests" \
  npm --prefix frontend run test -- \
  src/modules/workbench/ProjectDocumentationOverview.test.tsx \
  src/modules/workbench/ProjectWorkbench.test.tsx || overall=1

run_block "Focused workbench architecture tests" \
  uv run --project backend pytest \
  backend/tests/test_frontend_documentation_workbench_architecture.py \
  backend/tests/test_frontend_architecture.py -q || overall=1

section "Static 0010D contract"
{
  printf 'Governance endpoints : checklist, readiness, evidence, claims\n'
  printf 'Project stages       : unchanged six-stage contract\n'
  printf 'Policy duplication   : none in frontend component\n'
  printf 'Read-only integration: yes\n'
  printf 'Enterprise generation: absent\n'
  printf 'AI decision role     : none\n'
} >> "${TMP}"

run_block "Generate repository documentation" make docs || overall=1
run_block "Full repository quality gate" make verify || overall=1
run_block "Whitespace" git diff --check || overall=1

section "Changed paths"
git status --short >> "${TMP}" 2>&1 || overall=1

section "0010D boundaries"
cat >> "${TMP}" <<'BOUNDARIES'
- Existing Project stage URLs and Workspace context remain unchanged.
- Frontend consumes checklist/readiness/evidence/claims and does not recreate backend policy.
- Requirement, availability, readiness, lifecycle, and eligibility remain distinct.
- Missing-information remediation comes directly from backend findings.
- Traceability shows governed claims and directly referenced evidence metadata only.
- Unsupported future evidence kinds do not receive fake UI navigation.
- Archived Project governance remains readable.
- No enterprise document generator, claim authoring UI, AI drafting, or readiness rule change.
BOUNDARIES

section "Safety"
cat >> "${TMP}" <<'SAFETY'
- Audit reads repository source/tests/docs and executes local quality gates only.
- It does not print .env files, credentials, tokens, SQLite records, raw evidence payloads, or
  document contents.
- It does not contact live or external endpoints.
SAFETY

mv "${TMP}" "${REPORT}"
trap - EXIT

if [[ "${overall}" -eq 0 ]]; then
  printf '0010D project documentation workbench audit completed successfully.\n'
else
  printf '0010D project documentation workbench audit completed with findings.\n'
fi
printf 'Report: %s\n' "${REPORT}"
exit "${overall}"
