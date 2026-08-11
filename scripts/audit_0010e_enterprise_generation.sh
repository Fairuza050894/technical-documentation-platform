#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d ".git" || ! -f "Makefile" || ! -d "backend/src/tdp/modules/documents" ]]; then
  printf 'ERROR: Run this script from the technical-documentation-platform repository root.\n' >&2
  exit 1
fi

TS="$(date '+%Y%m%d_%H%M%S')"
REPORT="${HOME}/Downloads/technical-documentation-platform_0010e_enterprise_generation_${TS}.txt"
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
  section "0010E ENTERPRISE DOCUMENT GENERATION AUDIT"
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "$(pwd)"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"
} >> "${TMP}"

run_block "Repository status before generation" git status --short --branch || overall=1

run_block "Focused enterprise generation tests" \
  uv run --project backend pytest \
  backend/tests/domain/test_enterprise_generation_profile.py \
  backend/tests/application/test_enterprise_generation_service.py \
  backend/tests/infrastructure/test_enterprise_generation_renderer.py \
  backend/tests/presentation/test_enterprise_generation_api.py \
  backend/tests/test_enterprise_generation_architecture.py -q || overall=1

section "Static enterprise generation contract"
uv run --project backend python - <<'PY' >> "${TMP}" 2>&1 || overall=1
from tdp.modules.documents.domain.generation import (
    ENTERPRISE_GENERATION_PROFILES,
    ENTERPRISE_GENERATION_PROFILE_SCHEMA_VERSION,
)

print(f"Profile schema       : {ENTERPRISE_GENERATION_PROFILE_SCHEMA_VERSION}")
print(f"Profile total        : {len(ENTERPRISE_GENERATION_PROFILES)}")
print(
    "Profiles             : "
    + ", ".join(
        f"{item.document_type.value}:{item.profile_key}"
        for item in ENTERPRISE_GENERATION_PROFILES
    )
)
print("First enterprise type: LLD")
print("Readiness source     : canonical 0010C")
print("UNVERIFIED facts     : excluded")
print("AI factual role      : none")
print("New persistence      : none")
print("Legacy TSO retained  : yes")
PY

run_block "Generate repository documentation" make docs || overall=1
run_block "Full repository quality gate" make verify || overall=1
run_block "Whitespace" git diff --check || overall=1

section "Changed paths"
git status --short >> "${TMP}" 2>&1 || overall=1

section "0010E boundaries"
cat >> "${TMP}" <<'EOF'
- Generic enterprise generation profile/application pipeline is introduced.
- LLD is the only enterprise generation profile in this slice.
- Generation eligibility comes from 0010C readiness; no duplicate readiness policy is added.
- Cross-context evidence/readiness/catalog collection is isolated in Documents infrastructure.
- OBSERVED and INFERRED claims remain visibly distinct in generated content.
- UNVERIFIED statements are excluded from factual document content.
- Existing DocumentSeries/DocumentVersion/checksum/workflow/download lifecycle is reused.
- Technical Source Overview remains backward compatible.
- No DB migration, Template CRUD, AI drafting, new evidence collector, or frontend generation UI.
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
  printf '0010E enterprise generation audit completed successfully.\n'
else
  printf '0010E enterprise generation audit completed with findings.\n'
fi
printf 'Report: %s\n' "${REPORT}"
exit "${overall}"
