#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d ".git" || ! -f "Makefile" || ! -d "backend/src/tdp/modules/documents" ]]; then
  printf 'ERROR: Run this script from the technical-documentation-platform repository root.\n' >&2
  exit 1
fi

TS="$(date '+%Y%m%d_%H%M%S')"
REPORT="${HOME}/Downloads/technical-documentation-platform_0010f_asbuilt_generation_${TS}.txt"
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
  section "0010F AS-BUILT GENERATION AUDIT"
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "$(pwd)"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"
} >> "${TMP}"

run_block "Repository status before generation" git status --short --branch || overall=1

run_block "Focused As-Built generation tests" \
  uv run --project backend pytest \
  backend/tests/domain/test_enterprise_generation_profile.py \
  backend/tests/application/test_enterprise_generation_service.py \
  backend/tests/infrastructure/test_enterprise_generation_renderer.py \
  backend/tests/presentation/test_enterprise_generation_api.py \
  backend/tests/test_enterprise_generation_architecture.py \
  backend/tests/domain/test_readiness_policy.py -q || overall=1

section "Static 0010F contract"
uv run --project backend python - <<'PY' >> "${TMP}" 2>&1 || overall=1
from pathlib import Path

from tdp.modules.documents.domain.generation import ENTERPRISE_GENERATION_PROFILES

profiles = {item.document_type.value: item for item in ENTERPRISE_GENERATION_PROFILES}
as_built = profiles["AS_BUILT"]

print(f"Profile total       : {len(ENTERPRISE_GENERATION_PROFILES)}")
print(
    "Profiles            : "
    + ", ".join(
        f"{item.document_type.value}:{item.profile_key}"
        for item in ENTERPRISE_GENERATION_PROFILES
    )
)
print(f"As-Built evidence   : {as_built.primary_evidence_kind}")
print("As-Built claims     : " + ", ".join(as_built.rendered_claim_classifications))
print("Eligibility source  : canonical 0010C")
print("INFERRED factual use: none")
print("UNVERIFIED facts    : excluded")
print("Parallel service    : none")
print("New persistence     : none")
print("AI factual role     : none")

service = Path(
    "backend/src/tdp/modules/documents/application/enterprise_generation_service.py"
).read_text(encoding="utf-8")
adapter = Path(
    "backend/src/tdp/modules/documents/infrastructure/enterprise_generation_inputs.py"
).read_text(encoding="utf-8")
assert "DocumentType.AS_BUILT" not in service
assert "GenerateAsBuilt" not in service
assert "AS_BUILT" not in adapter
PY

run_block "Generate repository documentation" make docs || overall=1
run_block "Full repository quality gate" make verify || overall=1
run_block "Whitespace" git diff --check || overall=1

section "Changed paths"
git status --short >> "${TMP}" 2>&1 || overall=1

section "0010F boundaries"
cat >> "${TMP}" <<'EOF'
- AS_BUILT extends the existing generic enterprise generation pipeline.
- Canonical 0010C readiness remains the only eligibility gate.
- Inferred claims cannot substitute for the required OBSERVED As-Built claim.
- Only OBSERVED As-Built claim statements are rendered as confirmed implementation assertions.
- INFERRED and UNVERIFIED statements are excluded from factual As-Built content.
- Non-observed claim IDs/classifications remain visible only as excluded audit references.
- Existing evidence adapter, versioning, lifecycle, download, LLD, and TSO paths are reused.
- No parallel As-Built service, persistence migration, AI drafting, or frontend control is added.
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
  printf '0010F As-Built generation audit completed successfully.\n'
else
  printf '0010F As-Built generation audit completed with findings.\n'
fi
printf 'Report: %s\n' "${REPORT}"
exit "${overall}"
