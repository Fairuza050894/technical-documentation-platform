#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d ".git" || ! -f "Makefile" || ! -d "backend/src/tdp/modules/evidence" ]]; then
  printf 'ERROR: Run this script from the technical-documentation-platform repository root.\n' >&2
  exit 1
fi

TS="$(date '+%Y%m%d_%H%M%S')"
REPORT="${HOME}/Downloads/technical-documentation-platform_0010i_evidence_materialization_${TS}.txt"
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
  section "0010I GOVERNED EVIDENCE MATERIALIZATION AUDIT"
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "$(pwd)"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"
} >> "${TMP}"

run_block "Repository status before generation" git status --short --branch || overall=1

run_block "Focused materialization and readiness tests" \
  uv run --project backend pytest \
  backend/tests/domain/test_evidence_materialization.py \
  backend/tests/domain/test_evidence_claims.py \
  backend/tests/infrastructure/test_sqlite_evidence_repository.py \
  backend/tests/presentation/test_evidence_api.py \
  backend/tests/domain/test_readiness_policy.py \
  backend/tests/presentation/test_readiness_api.py \
  backend/tests/presentation/test_enterprise_generation_api.py \
  backend/tests/test_evidence_architecture.py -q || overall=1

section "Static 0010I contract"
uv run --project backend python - <<'PY' >> "${TMP}" 2>&1 || overall=1
from tdp.modules.evidence.domain.materialization import (
    SEMANTIC_EVIDENCE_MANIFEST_SCHEMA_VERSION,
)
from tdp.modules.readiness.domain.model import ReadinessRuleKind
from tdp.modules.readiness.domain.policy import (
    READINESS_POLICY_VERSION,
    readiness_profile,
)

print(f"Manifest schema       : {SEMANTIC_EVIDENCE_MANIFEST_SCHEMA_VERSION}")
print(f"Readiness policy      : {READINESS_POLICY_VERSION}")
print(
    "Semantic rule kind   : "
    f"{ReadinessRuleKind.MATERIALIZED_EVIDENCE_KIND.value}"
)
for document_type in (
    "USER_GUIDE",
    "INSTALLATION_GUIDE",
    "UAT_EVIDENCE",
    "JOURNEY_MAP",
):
    rule = readiness_profile(document_type).rules[0]
    print(f"{document_type:<20}: {rule.kind.value} / {rule.evidence_kind}")
print("Raw payload storage   : none")
print("External HTTP resolver: none")
print("AI materializer role  : none")
print("Installation generator: deferred")

assert SEMANTIC_EVIDENCE_MANIFEST_SCHEMA_VERSION == "semantic-evidence-manifest-v1"
assert READINESS_POLICY_VERSION == "document-readiness-v3"
assert all(
    readiness_profile(document_type).rules[0].kind
    is ReadinessRuleKind.MATERIALIZED_EVIDENCE_KIND
    for document_type in (
        "USER_GUIDE",
        "INSTALLATION_GUIDE",
        "UAT_EVIDENCE",
        "JOURNEY_MAP",
    )
)
PY

run_block "Generate repository documentation" make docs || overall=1
run_block "Full repository quality gate" make verify || overall=1
run_block "Whitespace" git diff --check || overall=1

section "Changed paths"
git status --short >> "${TMP}" 2>&1 || overall=1

section "0010I boundaries"
cat >> "${TMP}" <<'EOF'
- Referenced semantic Evidence Artifacts remain immutable provenance records.
- Typed semantic facts use semantic-evidence-manifest-v1 and deterministic canonical JSON.
- Materialization checksum must match the immutable Evidence Artifact checksum.
- Materializations are append-only in an additive table; existing Evidence/Claim rows are untouched.
- Registered but unmaterialized semantic evidence does not satisfy generation-oriented readiness.
- Readiness v3 exposes UNMATERIALIZED references instead of deferring failure to a generator.
- Direct file/HTTP references and common secret-bearing values are rejected in normalized facts.
- Raw evidence payloads, external resolvers, AI, browser/CI integration, and generators are absent.
- Installation Guide generation is deferred until document provenance is generalized truthfully.
EOF

section "Safety"
cat >> "${TMP}" <<'EOF'
- Audit executes local source/tests/docs/build checks only.
- It does not print .env files, credentials, tokens, SQLite records, canonical manifests, raw
  evidence payloads, claim statements, or generated document contents.
- It does not contact live or external endpoints.
EOF

mv "${TMP}" "${REPORT}"
trap - EXIT

if [[ "${overall}" -eq 0 ]]; then
  printf '0010I evidence materialization audit completed successfully.\n'
else
  printf '0010I evidence materialization audit completed with findings.\n'
fi
printf 'Report: %s\n' "${REPORT}"
exit "${overall}"
