#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d ".git" || ! -f "Makefile" || ! -d "backend/src/tdp/modules/readiness" ]]; then
  printf 'ERROR: Run this script from the technical-documentation-platform repository root.\n' >&2
  exit 1
fi

TS="$(date '+%Y%m%d_%H%M%S')"
REPORT="${HOME}/Downloads/technical-documentation-platform_0010c_document_readiness_${TS}.txt"
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
  section "0010C DOCUMENT READINESS AND MISSING INFORMATION AUDIT"
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "$(pwd)"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"
} >> "${TMP}"

run_block "Repository status before generation" git status --short --branch || overall=1

run_block "Focused readiness tests" \
  uv run --project backend pytest \
  backend/tests/domain/test_readiness_policy.py \
  backend/tests/presentation/test_readiness_api.py \
  backend/tests/test_readiness_architecture.py -q || overall=1

section "Static readiness contract"
uv run --project backend python - <<'PY' >> "${TMP}" 2>&1 || overall=1
from tdp.modules.readiness.domain.model import ReadinessFindingSeverity, ReadinessState
from tdp.modules.readiness.domain.policy import READINESS_POLICY_VERSION, READINESS_PROFILES

print(f"Policy version      : {READINESS_POLICY_VERSION}")
print(f"Profile total       : {len(READINESS_PROFILES)}")
print("Profile order       : " + ", ".join(item.document_type for item in READINESS_PROFILES))
print("States              : " + ", ".join(item.value for item in ReadinessState))
print("Finding severities  : " + ", ".join(item.value for item in ReadinessFindingSeverity))
print("Eligibility rule    : no BLOCKER")
print("Persistence         : computed, none")
print("AI decision role    : none")
PY

run_block "Generate repository documentation" make docs || overall=1
run_block "Full repository quality gate" make verify || overall=1
run_block "Whitespace" git diff --check || overall=1

section "Changed paths"
git status --short >> "${TMP}" 2>&1 || overall=1

section "0010C boundaries"
cat >> "${TMP}" <<'EOF'
- 0010A availability remains distinct from 0010C readiness.
- Readiness is computed from canonical Project, Evidence, Claim, and Document state.
- NOT_READY means at least one BLOCKER.
- PARTIALLY_READY means no blocker and at least one WARNING.
- READY means no blocker or warning.
- Eligibility is exactly the absence of blockers.
- As-Built requires direct OBSERVED evidence-backed claims.
- Unsupported evidence categories are reported as missing rather than fabricated.
- Project Handover requires approved versions of the required document bundle.
- No readiness persistence, document generation, AI drafting, or frontend redesign is introduced.
EOF

section "Safety"
cat >> "${TMP}" <<'EOF'
- Audit reads repository source/tests/docs and executes local quality gates only.
- It does not print .env files, credentials, tokens, SQLite records, evidence payloads, claim text,
  or document contents.
- It does not contact live or external endpoints.
EOF

mv "${TMP}" "${REPORT}"
trap - EXIT

if [[ "${overall}" -eq 0 ]]; then
  printf '0010C document readiness audit completed successfully.\n'
else
  printf '0010C document readiness audit completed with findings.\n'
fi
printf 'Report: %s\n' "${REPORT}"
exit "${overall}"
