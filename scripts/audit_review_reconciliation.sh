#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d ".git" || ! -f "Makefile" || ! -d "docs" ]]; then
  printf 'ERROR: Run this script from the technical-documentation-platform repository root.\n' >&2
  exit 1
fi

TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
DOWNLOADS_DIR="${HOME}/Downloads"
REPORT="${DOWNLOADS_DIR}/technical-documentation-platform_review_reconciliation_${TIMESTAMP}.txt"
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
  section "REVIEW RECONCILIATION AUDIT"
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "$(pwd)"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"
} >> "${TMP}"

run_block "Repository status before generation" git status --short --branch || overall=1

section "Required reconciliation files"
for path in \
  docs/governance/external-audit-response-2026-08.md \
  docs/product/roadmap.md \
  docs/requirements/mvp-1-enterprise-document-taxonomy-and-agentic-boundaries.md \
  scripts/audit_review_reconciliation.sh
do
  if [[ -f "${path}" ]]; then
    printf 'FOUND   %s\n' "${path}" >> "${TMP}"
  else
    printf 'MISSING %s\n' "${path}" >> "${TMP}"
    overall=1
  fi
done

section "Required policy signals"
check_signal() {
  local file="$1"
  local pattern="$2"
  local label="$3"
  if grep -Eq "${pattern}" "${file}"; then
    printf 'PASS %s\n' "${label}" >> "${TMP}"
  else
    printf 'FAIL %s\n' "${label}" >> "${TMP}"
    overall=1
  fi
}

check_signal docs/governance/external-audit-response-2026-08.md \
  'Partially addressed' 'partial disposition is defined'
check_signal docs/governance/external-audit-response-2026-08.md \
  'Dependency-blocked' 'dependency-blocked disposition is defined'
check_signal docs/governance/external-audit-response-2026-08.md \
  'HLD, LLD, As-Built, SOP, User Guide, Installation Guide, and Handover' \
  'enterprise taxonomy is reconciled'
check_signal docs/requirements/mvp-1-enterprise-document-taxonomy-and-agentic-boundaries.md \
  'OPENAPI_FILE' 'current source boundary is explicit'
check_signal docs/requirements/mvp-1-enterprise-document-taxonomy-and-agentic-boundaries.md \
  'TECHNICAL_SOURCE_OVERVIEW' 'current document boundary is explicit'
check_signal docs/requirements/mvp-1-enterprise-document-taxonomy-and-agentic-boundaries.md \
  'MCP remains read-only plus governed draft generation' \
  'MCP mutation guardrail is explicit'
check_signal docs/requirements/mvp-1-enterprise-document-taxonomy-and-agentic-boundaries.md \
  'SSRF' 'remote acquisition security boundary is explicit'
check_signal docs/product/roadmap.md \
  'As-Built and LLD Profiles' 'enterprise profile sequence is present'
check_signal docs/product/roadmap.md \
  'Reusable application composition root' 'automation dependency chain is present'

run_block "Generate repository documentation" make docs || overall=1
run_block "Documentation freshness and governance" make docs-check || overall=1
run_block "Full repository quality gate" make verify || overall=1
run_block "Whitespace" git diff --check || overall=1

section "Changed paths"
git status --short >> "${TMP}" 2>&1 || overall=1

section "Runtime-source isolation"
runtime_changes="$(
  git status --short |
    awk '{print $2}' |
    grep -E '^(backend/src|frontend/src)/' || true
)"
if [[ -z "${runtime_changes}" ]]; then
  printf 'PASS no backend/src or frontend/src changes in this documentation-only slice\n' >> "${TMP}"
else
  printf 'FAIL unexpected runtime source changes:\n%s\n' "${runtime_changes}" >> "${TMP}"
  overall=1
fi

section "Safety"
printf '%s\n' \
  "- The audit does not print .env values, credentials, tokens, or secret values." \
  "- SQLite data, runtime artifacts, imported evidence, and generated customer documents are excluded." \
  "- Live endpoints are not contacted." \
  >> "${TMP}"

mv "${TMP}" "${REPORT}"
trap - EXIT

if [[ "${overall}" -eq 0 ]]; then
  printf 'Review reconciliation audit completed successfully.\n'
else
  printf 'Review reconciliation audit completed with findings.\n'
fi
printf 'Report: %s\n' "${REPORT}"
exit "${overall}"
