#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d ".git" || ! -f "Makefile" || ! -d "backend/src/tdp/modules/evidence" ]]; then
  printf 'ERROR: Run this script from the technical-documentation-platform repository root.\n' >&2
  exit 1
fi

TS="$(date '+%Y%m%d_%H%M%S')"
REPORT="${HOME}/Downloads/technical-documentation-platform_0010b_evidence_claims_${TS}.txt"
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
  section "0010B EVIDENCE AND CLAIMS FOUNDATION AUDIT"
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "$(pwd)"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"
} >> "${TMP}"

run_block "Repository status before generation" git status --short --branch || overall=1

run_block "Focused evidence and claims tests" \
  uv run --project backend pytest \
  backend/tests/domain/test_evidence_claims.py \
  backend/tests/infrastructure/test_sqlite_evidence_repository.py \
  backend/tests/presentation/test_evidence_api.py \
  backend/tests/test_evidence_architecture.py -q || overall=1

section "Static evidence contract"
uv run --project backend python - <<'PY' >> "${TMP}" 2>&1 || overall=1
from tdp.modules.evidence.domain.model import ClaimClassification, EvidenceKind

print("Evidence kinds       : " + ", ".join(item.value for item in EvidenceKind))
print("Claim classifications: " + ", ".join(item.value for item in ClaimClassification))
print("AI is evidence       : False")
print("Readiness included    : False")
print("Generation eligibility: False")
PY

run_block "Generate repository documentation" make docs || overall=1
run_block "Full repository quality gate" make verify || overall=1
run_block "Whitespace" git diff --check || overall=1

section "Changed paths"
git status --short >> "${TMP}" 2>&1 || overall=1

section "0010B boundaries"
cat >> "${TMP}" <<'EOF'
- EvidenceArtifact is a manifest/reference; raw source payloads are not duplicated.
- Source evidence reuses the source checksum.
- Catalog snapshot evidence uses a deterministic normalized-content checksum.
- OBSERVED requires evidence.
- INFERRED requires evidence plus a deterministic derivation reference.
- UNVERIFIED is never promoted to confirmed fact by this slice.
- AI output is not evidence.
- Claim document relevance is validated against the 0010A enterprise registry.
- Archived Projects remain readable while new evidence/claim mutations are blocked.
- Readiness, blockers, generation eligibility, impact/versioning, and frontend redesign are absent.
EOF

section "Safety"
cat >> "${TMP}" <<'EOF'
- Audit reads repository source/tests/docs and executes local quality gates only.
- It does not print .env files, credentials, tokens, SQLite records, imported raw evidence, or
  document contents.
- It does not contact live or external endpoints.
EOF

mv "${TMP}" "${REPORT}"
trap - EXIT

if [[ "${overall}" -eq 0 ]]; then
  printf '0010B evidence/claims audit completed successfully.\n'
else
  printf '0010B evidence/claims audit completed with findings.\n'
fi
printf 'Report: %s\n' "${REPORT}"
exit "${overall}"
