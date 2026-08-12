#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d ".git" || ! -f "Makefile" || ! -d "backend/src/tdp/modules/evidence" ]]; then
  printf 'ERROR: Run this script from the technical-documentation-platform repository root.\n' >&2
  exit 1
fi

TS="$(date '+%Y%m%d_%H%M%S')"
REPORT="${HOME}/Downloads/technical-documentation-platform_0010h_evidence_capability_${TS}.txt"
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
  section "0010H EVIDENCE CAPABILITY AUDIT"
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "$(pwd)"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"
} >> "${TMP}"

run_block "Repository status before generation" git status --short --branch || overall=1

run_block "Focused evidence capability tests" \
  uv run --project backend pytest \
  backend/tests/domain/test_evidence_claims.py \
  backend/tests/infrastructure/test_sqlite_evidence_repository.py \
  backend/tests/presentation/test_evidence_api.py \
  backend/tests/domain/test_readiness_policy.py \
  backend/tests/presentation/test_readiness_api.py \
  backend/tests/presentation/test_enterprise_generation_api.py \
  backend/tests/test_evidence_architecture.py -q || overall=1

section "Static 0010H contract"
uv run --project backend python - <<'PY' >> "${TMP}" 2>&1 || overall=1
from tdp.modules.evidence.domain.model import (
    EvidenceCollectionMethod,
    EvidenceKind,
    EvidenceSourceSystem,
    REFERENCED_EVIDENCE_KINDS,
)
from tdp.modules.readiness.domain.policy import (
    READINESS_POLICY_VERSION,
    readiness_profile,
)

print("Evidence kinds      : " + ", ".join(item.value for item in EvidenceKind))
print(
    "Referenced kinds    : "
    + ", ".join(item.value for item in REFERENCED_EVIDENCE_KINDS)
)
print(f"Reference source    : {EvidenceSourceSystem.GOVERNED_REFERENCE.value}")
print(
    f"Reference method    : {EvidenceCollectionMethod.REFERENCE_REGISTRATION.value}"
)
print(f"Readiness policy    : {READINESS_POLICY_VERSION}")
hld = readiness_profile("HLD").rules[0]
onboarding = readiness_profile("DEVELOPER_ONBOARDING_BRIEF").rules[0]
print(f"HLD rule kind       : {hld.kind.value}")
print("HLD technical kinds : " + ", ".join(hld.evidence_kinds))
print("Onboarding kinds    : " + ", ".join(onboarding.evidence_kinds))
print("Evidence migration  : none")
print("Raw payload storage : none")
print("AI evidence role    : none")

assert [item.value for item in REFERENCED_EVIDENCE_KINDS] == [
    "USER_JOURNEY",
    "DEPLOYMENT_RUNTIME",
    "UAT_RESULT",
]
assert READINESS_POLICY_VERSION == "document-readiness-v2"
assert hld.evidence_kinds == ("SOURCE_ARTIFACT", "CATALOG_SNAPSHOT")
assert onboarding.evidence_kinds == ("SOURCE_ARTIFACT", "CATALOG_SNAPSHOT")
PY

run_block "Generate repository documentation" make docs || overall=1
run_block "Full repository quality gate" make verify || overall=1
run_block "Whitespace" git diff --check || overall=1

section "Changed paths"
git status --short >> "${TMP}" 2>&1 || overall=1

section "0010H boundaries"
cat >> "${TMP}" <<'EOF'
- EvidenceKind now includes USER_JOURNEY, DEPLOYMENT_RUNTIME, and UAT_RESULT.
- Referenced semantic evidence stores immutable provenance manifests, not raw payloads.
- Clients cannot choose source-system or collection-method classification.
- Exact kind/origin retries are idempotent; conflicting immutable provenance is rejected.
- Existing Evidence SQLite schema and append-only triggers are reused without migration.
- Readiness policy v2 prevents semantic evidence from satisfying HLD/Onboarding technical blockers.
- User Guide, Journey Map, Installation Guide, and UAT Evidence consume only their explicit kinds.
- No document generator, browser/CI/UAT collector, AI drafting, MCP, or frontend authoring UI is added.
EOF

section "Safety"
cat >> "${TMP}" <<'EOF'
- Audit executes local source/tests/docs/build checks only.
- It does not print .env files, credentials, tokens, SQLite records, raw evidence payloads, claim
  statements, or generated document contents.
- It does not contact live or external endpoints.
EOF

mv "${TMP}" "${REPORT}"
trap - EXIT

if [[ "${overall}" -eq 0 ]]; then
  printf '0010H evidence capability audit completed successfully.\n'
else
  printf '0010H evidence capability audit completed with findings.\n'
fi
printf 'Report: %s\n' "${REPORT}"
exit "${overall}"
