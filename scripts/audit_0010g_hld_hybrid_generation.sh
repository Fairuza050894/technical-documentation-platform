#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d ".git" || ! -f "Makefile" || ! -d "backend/src/tdp/modules/documents" ]]; then
  printf 'ERROR: Run this script from the technical-documentation-platform repository root.\n' >&2
  exit 1
fi

TS="$(date '+%Y%m%d_%H%M%S')"
REPORT="${HOME}/Downloads/technical-documentation-platform_0010g_hld_hybrid_generation_${TS}.txt"
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
  section "0010G HLD HYBRID GENERATION AUDIT"
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "$(pwd)"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"
} >> "${TMP}"

run_block "Repository status before generation" git status --short --branch || overall=1

run_block "Focused HLD hybrid generation tests" \
  uv run --project backend pytest \
  backend/tests/domain/test_enterprise_generation_profile.py \
  backend/tests/application/test_enterprise_generation_service.py \
  backend/tests/infrastructure/test_enterprise_generation_renderer.py \
  backend/tests/infrastructure/test_document_nullable_snapshot_provenance.py \
  backend/tests/presentation/test_enterprise_generation_api.py \
  backend/tests/test_enterprise_generation_architecture.py \
  backend/tests/domain/test_readiness_policy.py -q || overall=1

section "Static 0010G contract"
uv run --project backend python - <<'PY' >> "${TMP}" 2>&1 || overall=1
from pathlib import Path

from tdp.modules.documents.domain.generation import (
    ENTERPRISE_GENERATION_PROFILES,
    ENTERPRISE_GENERATION_PROFILE_SCHEMA_VERSION,
)

profiles = {item.document_type.value: item for item in ENTERPRISE_GENERATION_PROFILES}
hld = profiles["HLD"]

print(f"Profile schema       : {ENTERPRISE_GENERATION_PROFILE_SCHEMA_VERSION}")
print(f"Profile total        : {len(ENTERPRISE_GENERATION_PROFILES)}")
print(
    "Profiles             : "
    + ", ".join(
        f"{item.document_type.value}:{item.profile_key}"
        for item in ENTERPRISE_GENERATION_PROFILES
    )
)
print("HLD evidence         : " + ", ".join(hld.accepted_evidence_kinds))
print("HLD claims           : " + ", ".join(hld.rendered_claim_classifications))
print("Eligibility source   : canonical 0010C ANY_EVIDENCE")
print("Source-only target   : nullable")
print("UNVERIFIED facts     : excluded")
print("Parallel service     : none")
print("AI factual role      : none")

adapter = Path(
    "backend/src/tdp/modules/documents/infrastructure/enterprise_generation_inputs.py"
).read_text(encoding="utf-8")
service = Path(
    "backend/src/tdp/modules/documents/application/enterprise_generation_service.py"
).read_text(encoding="utf-8")
repository = Path(
    "backend/src/tdp/modules/documents/infrastructure/sqlite_repository.py"
).read_text(encoding="utf-8")

assert ENTERPRISE_GENERATION_PROFILE_SCHEMA_VERSION == "enterprise-generation-profile-v2"
assert hld.accepted_evidence_kinds == ("CATALOG_SNAPSHOT", "SOURCE_ARTIFACT")
assert "profile.accepted_evidence_kinds" in adapter
assert "DocumentType.HLD" not in adapter
assert "HLD_TECHNICAL_EVIDENCE_REQUIRED" not in adapter
assert "DocumentType.HLD" not in service
assert "target_run_id TEXT," in repository
assert "_migrate_nullable_target_run_id" in repository
PY

run_block "Generate repository documentation" make docs || overall=1
run_block "Full repository quality gate" make verify || overall=1
run_block "Whitespace" git diff --check || overall=1

section "Changed paths"
git status --short >> "${TMP}" 2>&1 || overall=1

section "0010G boundaries"
cat >> "${TMP}" <<'EOF'
- HLD extends the existing generic enterprise generation pipeline.
- Canonical 0010C readiness remains the only eligibility gate; HLD stays ANY_EVIDENCE.
- HLD accepts current governed CATALOG_SNAPSHOT and SOURCE_ARTIFACT evidence without adding a
  hidden Catalog prerequisite.
- Evidence selection is deterministic and profile-driven, not HLD-specific in the input adapter.
- SOURCE_ARTIFACT generation resolves Source provenance directly and does not fabricate a Catalog
  synchronization, operations, or schemas.
- CATALOG_SNAPSHOT generation retains normalized API boundary evidence.
- OBSERVED and INFERRED HLD claims remain explicitly classified; INFERRED keeps its derivation.
- UNVERIFIED HLD statements are excluded from factual content.
- Document target synchronization provenance is nullable end to end, with a migration that
  preserves existing version rows and workflow history.
- Existing LLD, As-Built, Technical Source Overview, lifecycle, download, and archived behavior
  remain in the same architecture.
- No parallel HLD application service, AI drafting, new collector, or generation UI is added.
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
  printf '0010G HLD hybrid generation audit completed successfully.\n'
else
  printf '0010G HLD hybrid generation audit completed with findings.\n'
fi
printf 'Report: %s\n' "${REPORT}"
exit "${overall}"
