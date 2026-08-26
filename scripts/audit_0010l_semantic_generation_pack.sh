#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d ".git" || ! -f "Makefile" || ! -d "backend/src/tdp/modules/documents" ]]; then
  printf 'ERROR: Run from the technical-documentation-platform repository root.\n' >&2
  exit 1
fi

TS="$(date '+%Y%m%d_%H%M%S')"
REPORT="${HOME}/Downloads/technical-documentation-platform_0010l_semantic_generation_pack_${TS}.txt"
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
  section "0010L SEMANTIC DOCUMENT GENERATION PACK AUDIT"
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "$(pwd)"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"
} >> "${TMP}"

run_block "Repository status before generation" git status --short --branch || overall=1

run_block "Focused semantic generation backend tests" \
  uv run --project backend pytest \
  backend/tests/domain/test_semantic_generation_profiles.py \
  backend/tests/presentation/test_semantic_generation_pack_api.py \
  backend/tests/domain/test_document_provenance.py \
  backend/tests/test_enterprise_generation_architecture.py -q || overall=1

run_block "Focused Documents workspace test" \
  npm --prefix frontend run test -- \
  src/modules/documents/DocumentsWorkspace.test.tsx || overall=1

section "Static 0010L contract"
uv run --project backend python - <<'PY' >> "${TMP}" 2>&1 || overall=1
from tdp.modules.documents.domain.generation import enterprise_generation_profile
from tdp.modules.documents.domain.model import DocumentType

expected = {
    DocumentType.USER_GUIDE: ("enterprise-user-guide-v1", "USER_JOURNEY"),
    DocumentType.INSTALLATION_GUIDE: (
        "enterprise-installation-guide-v1",
        "DEPLOYMENT_RUNTIME",
    ),
    DocumentType.UAT_EVIDENCE: ("enterprise-uat-evidence-v1", "UAT_RESULT"),
    DocumentType.JOURNEY_MAP: ("enterprise-journey-map-v1", "USER_JOURNEY"),
}

for document_type, (profile_key, evidence_kind) in expected.items():
    profile = enterprise_generation_profile(document_type)
    assert profile is not None
    assert profile.profile_key == profile_key
    assert profile.accepted_evidence_kinds == (evidence_kind,)
    print(f"{document_type.value:20} : {profile_key} <- {evidence_kind}")

print("Readiness gate        : document-readiness-v3")
print("Source identity       : nullable for semantic generation")
print("External resolver     : none")
print("Raw payload copy      : none")
print("AI factual role       : none")
print("SOP/Handover generator: deferred")
PY

run_block "Generate repository documentation" make docs || overall=1
run_block "Full repository quality gate" make verify || overall=1
run_block "Whitespace" git diff --check || overall=1

section "Changed paths"
git status --short >> "${TMP}" 2>&1 || overall=1

section "0010L boundaries"
cat >> "${TMP}" <<'EOF_0010L_BOUNDARIES'
- USER_GUIDE and JOURNEY_MAP consume materialized USER_JOURNEY evidence.
- INSTALLATION_GUIDE consumes materialized DEPLOYMENT_RUNTIME evidence.
- UAT_EVIDENCE consumes materialized UAT_RESULT evidence.
- Readiness v3 remains the only eligibility policy.
- Registered-only semantic evidence cannot generate a document.
- Semantic Document Versions may have null source_id and target_run_id.
- Documents provenance stores Evidence Artifact ID/kind/checksum, not materialized payloads.
- Existing HLD, LLD, As-Built, Technical Source Overview, review, download, and version lifecycle remain.
- No external HTTP/file resolver, raw payload persistence, AI factual generation, browser, CI/UAT
  collector, SOP generator, Handover generator, or MCP is introduced.
EOF_0010L_BOUNDARIES

section "Safety"
cat >> "${TMP}" <<'EOF_0010L_SAFETY'
- Audit executes repository-local source/tests/docs/build checks only.
- It does not print .env files, credentials, tokens, evidence manifest payloads, claims, or generated
  document bodies.
- It does not contact live or external endpoints.
EOF_0010L_SAFETY

mv "${TMP}" "${REPORT}"
trap - EXIT

if [[ "${overall}" -eq 0 ]]; then
  printf '0010L semantic generation pack audit completed successfully.\n'
else
  printf '0010L semantic generation pack audit completed with findings.\n'
fi
printf 'Report: %s\n' "${REPORT}"
exit "${overall}"
